export type TopicCard = {
  id: string
  title: string
  genre: string
  mood: string
  hook: string
  tags: string[]
  why_trending: string
}

export type TrendingTopicsResponse = {
  region: string
  region_name: string
  state: string
  topics: TopicCard[]
}
