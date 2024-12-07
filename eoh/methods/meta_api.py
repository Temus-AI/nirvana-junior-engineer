import http.client
import json
import os
import re
import urllib.parse
from typing import Any, Callable, Dict, Optional

import httpx
import requests
from bs4 import BeautifulSoup
from langchain_community.document_transformers import Html2TextTransformer
from langchain_core.documents import Document

from .evolnode import QueryEngine
from .llm import get_openai_response
from .meta_prompt import (
    CHOOSE_USEFUL_LINKS,
    GENERATE_NODES_FROM_DOCS,
    GENERATE_NODES_FROM_GUIDE,
    PAGE_CLASSIFIER,
    MetaPrompt,
    PromptMode,
    extract_json_from_text,
    extract_python_funcions,
)
from .population import Evolution


def nodes_from_api_deprecated(
    link: str,
    clean: bool = True,
    get_response: Optional[Callable] = get_openai_response,
    evol_method: str = "i1",
    max_attempts: int = 3,
):
    from .population import Evolution

    resp = requests.get(link)
    if resp.status_code != 200:
        return "Error: Unable to fetch API documentation"
    content = resp.text.split("<body>")[1].split("</body>")[0].strip()
    qe = QueryEngine()
    nodes = qe.meta_prompts
    if clean:
        content = re.sub(r"<(/?)(\w+)[^>]*>", r"<\1\2>", content)
        content = re.sub(r"</?span>", "", content)
    prompt = (
        content
        + "\nAvailable functions for use:\n"
        + "\n".join([node.__repr__() for node in nodes])
        + "\nYou are a Turing Prize winner programmer."
        + GENERATE_NODES_FROM_DOCS
    )
    nodes = []
    for _ in range(max_attempts):
        response = get_response(prompt)
        response = response if type(response) is str else response[0]
        try:
            node_dict = extract_json_from_text(response)["nodes"]
            for node in node_dict:
                meta_prompt = MetaPrompt(
                    task=node.get("task"),
                    func_name=node.get("name"),
                    inputs=node.get("inputs"),
                    outputs=node.get("outputs"),
                    input_types=node.get("input_types"),
                    output_types=node.get("output_types"),
                    mode=PromptMode((node.get("mode", "code")).lower()),
                )
                nodes.append(
                    (
                        Evolution(
                            pop_size=1,
                            meta_prompt=meta_prompt,
                            get_response=get_response,
                        ),
                        node.get("relevant_docs"),
                    )
                )
            break
        except ValueError as e:
            print(f"Failed to extract JSON from API plan response: {e}")
        except KeyError as e:
            nodes = []
            print(f"Failed to extract fully formed nodes from API plan response: {e}")

    for node in nodes:
        node[0].get_offspring(evol_method, feedback=node[1])
    return nodes


def _search_google(query: str) -> Dict[str, Any]:
    """
    Use Serper API to search Google for information

    Args:
        query (str): The search query

    Returns:
        Dict[str, Any]: Parsed JSON response from the API
    """
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({"q": query})
    headers = {
        "X-API-KEY": os.environ["SERPER_API_KEY"],
        "Content-Type": "application/json",
    }

    try:
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        print(f"Error occurred during API request: {str(e)}")
        return {}
    finally:
        conn.close()


def nodes_from_api(
    api_name: str,
    max_links: int = None,
    get_response: Optional[Callable] = get_openai_response,
    evol_method: str = "i1",
    max_attempts: int = 3,
):
    def get_content(link):
        res = httpx.get(link, follow_redirects=True)
        res.raise_for_status()
        url = str(res.url)

        return res.text, url

    link = _search_google(f"{api_name} python docs")["organic"][0]["link"]
    domain = urllib.parse.urlparse(link).netloc
    try:
        content, url = get_content(link)
    except httpx.HTTPStatusError as e:
        print(f"Error occurred during request: {str(e)}")
        return []

    htmls = [content]
    links = [url]
    ptr = 0
    while ptr < len(links):
        soup = BeautifulSoup(htmls[ptr], "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            new_link = urllib.parse.urljoin(links[ptr], href.split("#")[0])
            parse = urllib.parse.urlparse(new_link)
            if (
                parse.netloc == domain
                and new_link not in links
                and new_link + "/" not in links
                and parse.scheme in ["http", "https"]
            ):
                try:
                    content, url = get_content(new_link)
                    htmls.append(content)
                    links.append(url)
                except httpx.HTTPStatusError as e:
                    print(f"Error occurred during request: {str(e)}")
        ptr += 1
    prompt = CHOOSE_USEFUL_LINKS
    if max_links is not None:
        prompt += f"\nOnly choose maximum {max_links} links as the junior developer does not have time or people will die. Only choose the most useful links."
    prompt += f"\nLinks: {links}"
    response = get_response(prompt)
    response = response if type(response) is str else response[0]
    indexes = extract_json_from_text(response)["links"]
    htmls = [htmls[i] for i in indexes]

    docs = [Document(page_content=html) for html in htmls]
    html2text = Html2TextTransformer()
    docs_transformed = html2text.transform_documents(docs)
    texts = [doc_transformed.page_content for doc_transformed in docs_transformed]

    doc_nodes = []
    guide_nodes = []
    for text in texts:
        prompt = text + PAGE_CLASSIFIER
        response = get_response(prompt)
        response = response if type(response) is str else response[0]
        classification = extract_json_from_text(response)["class"]
        if classification == "useless":
            continue
        elif classification == "tutorial":
            prompt = text + GENERATE_NODES_FROM_GUIDE
        else:
            prompt = text + GENERATE_NODES_FROM_DOCS
        nodes = []
        for _ in range(max_attempts):
            response = get_response(prompt)
            response = response if type(response) is str else response[0]
            try:
                node_dict = extract_json_from_text(response)["nodes"]
                for node in node_dict:
                    meta_prompt = MetaPrompt(
                        task=node.get("task"),
                        func_name=node.get("name"),
                        inputs=node.get("inputs"),
                        outputs=node.get("outputs"),
                        input_types=node.get("input_types"),
                        output_types=node.get("output_types"),
                        mode=PromptMode((node.get("mode", "code")).lower()),
                    )
                    evol = Evolution(
                        pop_size=1,
                        meta_prompt=meta_prompt,
                        get_response=get_response,
                        test_cases=node.get("tests"),
                        custom_metric_map=node.get("metric_map"),
                    )
                    if classification == "documentation":
                        nodes.append(
                            (
                                evol,
                                node.get("relevant_docs"),
                            )
                        )
                    elif classification == "tutorial":
                        evol.evol.reasoning = node.get("reasoning")
                        code = extract_python_funcions(response)
                        evol.evol.code = code
                        guide_nodes.append(evol)
                break
            except ValueError as e:
                print(f"Failed to extract JSON from API plan response: {e}")
            except KeyError as e:
                nodes = []
                print(
                    f"Failed to extract fully formed nodes from API plan response: {e}"
                )
            except Exception as e:
                nodes = []
                print(f"Error occurred: {e}")

        doc_nodes += nodes
    for node in doc_nodes:
        node[0].get_offspring(evol_method, feedback=node[1])
    return doc_nodes, guide_nodes
