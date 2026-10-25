import { api } from '../services/api'
import { Meta } from '../services/types'
import { useFetch } from './useFetch'

export function useMeta() {
  return useFetch<Meta>(async () => (await api.get<Meta>('/meta')).data, [])
}
