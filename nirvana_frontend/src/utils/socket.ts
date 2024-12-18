export const socketPath = `wss://temus.herokuapp.com/`

// export const webSocketServer = new WebSocket(socketPath)

export interface WebSocketMessageType {
  message: string
  id: string
}

export interface EntityType {
  value: string
  offset: number
  length: number
  type: 'NOUN' | 'VERB' | 'PROPN' | 'NUM' | 'SYM' | 'MISC'
}

export type EntityKeys =
  | 'misc'
  | 'noun'
  | 'number'
  | 'proper_noun'
  | 'symbol'
  | 'verb'

export type Tokenization = {
  [key in EntityKeys as string]: EntityType[]
}

export const emptyTokenization: Tokenization = {
  misc: [],
  noun: [],
  number: [],
  proper_noun: [],
  symbol: [],
  verb: [],
}

export interface WebSocketResponseType {
  entities: Tokenization
  id: string
}

// webSocketServer.onopen = () => {
//   console.log('[connected to temus heroku server]')
// }
