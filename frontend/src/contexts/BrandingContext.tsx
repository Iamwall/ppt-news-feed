import React, { createContext, useContext, useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '../api/client'

export interface Branding {
  app_name: string
  tagline: string
  primary_color: string
  secondary_color: string
  newsletter_title: string
  footer_text: string
  item_terminology: string
  item_terminology_plural: string
}

export interface Domain {
  id: string
  name: string
  description: string
  icon: string
  primary_color: string
}

interface BrandingContextType {
  branding: Branding | null
  domains: Domain[]
  activeDomainId: string | null
  isLoading: boolean
  setActiveDomain: (domainId: string) => Promise<void>
}

const defaultBranding: Branding = {
  app_name: 'Science Digest',
  tagline: 'Your daily dose of scientific discovery',
  primary_color: '#0984e3',
  secondary_color: '#6c5ce7',
  newsletter_title: 'Science Digest Newsletter',
  footer_text: 'Stay curious!',
  item_terminology: 'paper',
  item_terminology_plural: 'papers',
}

const BrandingContext = createContext<BrandingContextType>({
  branding: defaultBranding,
  domains: [],
  activeDomainId: null,
  isLoading: true,
  setActiveDomain: async () => {},
})

export const useBranding = () => useContext(BrandingContext)

export const BrandingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient()
  const [activeDomainId, setActiveDomainId] = useState<string | null>(null)

  // Fetch current branding
  const { data: brandingData, isLoading: brandingLoading } = useQuery({
    queryKey: ['branding'],
    queryFn: async () => {
      const response = await settingsApi.getBranding()
      return response.data as Branding & { domain_id: string }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Fetch available domains
  const { data: domainsData, isLoading: domainsLoading } = useQuery({
    queryKey: ['domains'],
    queryFn: async () => {
      const response = await settingsApi.getDomains()
      return response.data.domains as Domain[]
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  })

  // Set active domain mutation
  const setDomainMutation = useMutation({
    mutationFn: async (domainId: string) => {
      await settingsApi.setActiveDomain(domainId)
      return domainId
    },
    onSuccess: () => {
      // Invalidate branding to refetch with new domain
      queryClient.invalidateQueries({ queryKey: ['branding'] })
    },
  })

  // Update activeDomainId when branding loads
  useEffect(() => {
    if (brandingData && 'domain_id' in brandingData) {
      setActiveDomainId(brandingData.domain_id)
    }
  }, [brandingData])

  const handleSetActiveDomain = async (domainId: string) => {
    await setDomainMutation.mutateAsync(domainId)
    setActiveDomainId(domainId)
  }

  // Apply primary color as CSS variable
  useEffect(() => {
    if (brandingData?.primary_color) {
      document.documentElement.style.setProperty('--primary-color', brandingData.primary_color)
      document.documentElement.style.setProperty('--secondary-color', brandingData.secondary_color || '#6c5ce7')
    }
  }, [brandingData])

  const value: BrandingContextType = {
    branding: brandingData || defaultBranding,
    domains: domainsData || [],
    activeDomainId,
    isLoading: brandingLoading || domainsLoading,
    setActiveDomain: handleSetActiveDomain,
  }

  return (
    <BrandingContext.Provider value={value}>
      {children}
    </BrandingContext.Provider>
  )
}
