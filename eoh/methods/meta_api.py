import asyncio
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
from tiny_dag import add_nodes, get_graph_state

from .evolnode import QueryEngine
from .llm import get_openai_response
from .meta_prompt import (
    CHOOSE_USEFUL_LINKS,
    GENERATE_NODES_FROM_DOCS,
    GENERATE_NODES_FROM_GUIDE,
    PAGE_CLASSIFIER,
    MetaPrompt,
    extract_json_from_text,
    extract_python_funcions,
    get_prompt_mode,
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
                    mode=get_prompt_mode(node.get("mode", "code").lower()),
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


async def aget_content(link, client):
    res = await client.get(link, follow_redirects=True)
    if res.status_code == 200:
        url = str(res.url)
        return res.text, url
    else:
        return "", ""


def nodes_from_api(
    api_name: str,
    max_links: int = None,
    fast_response: Optional[Callable] = get_openai_response,
    slow_response: Optional[Callable] = get_openai_response,
    evol_method: str = "i1",
    creation_max_attempts: int = 3,
    node_max_attempts: int = 3,
    view_on_frontend: bool = False,
):
    import nest_asyncio

    nest_asyncio.apply()

    limits = httpx.Limits(max_keepalive_connections=None, max_connections=None)
    client = httpx.AsyncClient(timeout=None, limits=limits)
    webpages = []
    visit = set()
    dependency_dict = {}

    async def recursive_search(link, ref_url=None, parent=None):
        nonlocal webpages, visit, dependency_dict, client
        content, url = await aget_content(link, client)
        if ref_url is None:
            ref_url = url
        if url and content:
            if parent is not None:
                dependency_dict[parent] = dependency_dict.get(parent, []) + [url]
            webpages.append((url, content))
            visit.add(url)
        soup = BeautifulSoup(content, "html.parser")
        new_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            new_link = urllib.parse.urljoin(link, href.split("#")[0])
            parse = urllib.parse.urlparse(new_link)
            if (
                ref_url in new_link
                and new_link not in visit
                and new_link + "/" not in visit
                and parse.scheme in ["http", "https"]
            ):
                visit.add(new_link)
                new_links.append(new_link)
        await asyncio.gather(
            *[recursive_search(new_link, ref_url, link) for new_link in new_links]
        )

    link = _search_google(f"{api_name} python docs")["organic"][0]["link"]
    print("Scraping links")
    asyncio.run(recursive_search(link))

    asyncio.run(client.aclose())

    links, htmls = zip(*webpages)

    print("Choosing and preprocessing links")
    prompt = CHOOSE_USEFUL_LINKS
    if max_links is not None:
        prompt += f"\nOnly choose maximum {max_links} links as the junior developer does not have time or people will die. Only choose the most useful links."
    prompt += f"\nLinks: {links}"
    responses = fast_response([prompt] * 20)
    for response in responses:
        try:
            indexes = extract_json_from_text(response)["links"]
            htmls = [htmls[i] for i in indexes]
            break
        except Exception:
            continue
    docs = [Document(page_content=html) for html in htmls]
    html2text = Html2TextTransformer()
    docs_transformed = html2text.transform_documents(docs)
    texts = [doc_transformed.page_content for doc_transformed in docs_transformed]

    doc_nodes = []
    guide_nodes = []
    print("Classifying links and extracting nodes")
    for text in texts:
        prompt = text + PAGE_CLASSIFIER
        responses = fast_response([prompt] * 30)
        classification = "useless"
        for response in responses:
            try:
                classification = extract_json_from_text(response)["class"]
                break
            except Exception:
                continue
        if classification == "useless":
            continue
        elif classification == "tutorial":
            prompt = text + GENERATE_NODES_FROM_GUIDE
        else:
            prompt = text + GENERATE_NODES_FROM_DOCS
        nodes = []
        for _ in range(creation_max_attempts):
            response = slow_response(prompt)
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
                        mode=get_prompt_mode(node.get("mode", "code").lower()),
                    )
                    evol = Evolution(
                        meta_prompt=meta_prompt,
                        get_response=fast_response,
                        test_cases=[
                            (test["input"], test["output"])
                            for test in node.get("tests")
                        ]
                        if type(node.get("tests")) is list
                        else (node.get("tests")["input"], node.get("tests")["output"]),
                        custom_metric_map=node.get("metric_map"),
                        pop_size=node_max_attempts,
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
            # except Exception as e:
            #     nodes = []
            #     print(f"Error occurred: {e}")

        doc_nodes += nodes
    for node in doc_nodes:
        node[0].get_offspring(evol_method, feedback=node[1])

    for node in guide_nodes:
        node.evol._evaluate_fitness(custom_metric_map=node.evol.custom_metric_map)

    if view_on_frontend:
        graph = get_graph_state()
        max_idx = max([node["id"] for node in graph["nodes"]])
        frontend_nodes = []
        for idx, node in enumerate(doc_nodes, max_idx + 1):
            frontend_nodes.append(
                {
                    "id": idx,
                    "x": 0,
                    "y": 0,
                    "name": " ".join(node[0].meta_prompt.func_name.split("_")).title(),
                    "target": "",
                    "input": node[0].meta_prompt.inputs,
                    "output": node[0].meta_prompt.outputs,
                    "code": node[0].evol.code,
                    "fitness": node[0].evol.fitness,
                    "reasoning": node[0].evol.reasoning,
                    "inputTypes": node[0].meta_prompt.input_types,
                    "outputTypes": node[0].meta_prompt.output_types,
                }
            )

        for idx, node in enumerate(guide_nodes, idx + 1):
            frontend_nodes.append(
                {
                    "id": idx,
                    "x": 0,
                    "y": 0,
                    "name": " ".join(node.meta_prompt.func_name.split("_")).title(),
                    "target": "",
                    "input": node.meta_prompt.inputs,
                    "output": node.meta_prompt.outputs,
                    "code": node.evol.code,
                    "fitness": node.evol.fitness,
                    "reasoning": node.evol.reasoning,
                    "inputTypes": node.meta_prompt.input_types,
                    "outputTypes": node.meta_prompt.output_types,
                }
            )
        add_nodes(frontend_nodes, [])

    return doc_nodes, guide_nodes
