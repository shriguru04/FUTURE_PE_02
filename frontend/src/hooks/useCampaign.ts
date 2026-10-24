import { api } from '../services/api'
import { Campaign } from '../services/types'
import { useFetch } from './useFetch'

export const useCampaign = (id: string) => useFetch(async () => (await api.get<Campaign>(`/campaigns/${id}`)).data, [id])
