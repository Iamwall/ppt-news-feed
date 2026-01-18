import { useEffect, useRef, useState, useCallback } from 'react'
import { PulsePaper } from '../api/client'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'

interface UseLiveFeedOptions {
  domainId?: string
  active?: boolean
  onNewItem?: (item: PulsePaper) => void
  onBreakingAlert?: (item: PulsePaper) => void
}

type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export function useLiveFeed({ domainId, active = true, onNewItem, onBreakingAlert }: UseLiveFeedOptions) {
  const [status, setStatus] = useState<WebSocketStatus>('disconnected')
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const queryClient = useQueryClient()

  // Construct WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    // Get base API URL from env or default
    const apiUrl = import.meta.env.VITE_API_URL || '/api/v1/'
    
    // Determine protocol (ws:// or wss://)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    
    let host = window.location.host
    let path = apiUrl
    
    if (apiUrl.startsWith('http')) {
        const url = new URL(apiUrl)
        host = url.host
        path = url.pathname
    } else if (apiUrl.startsWith('/')) {
        // Relative path, use current host
    }

    // Ensure path ends with slash for joining
    if (!path.endsWith('/')) path += '/'

    const wsEndpoint = domainId ? `ws/pulse/${domainId}` : 'ws/pulse'
    return `${protocol}//${host}${path}${wsEndpoint}`
  }, [domainId])

  const connect = useCallback(() => {
    if (!active) return

    const url = getWebSocketUrl()
    console.log('[LivePulse] Connecting to:', url)
    
    setStatus('connecting')
    const ws = new WebSocket(url)

    ws.onopen = () => {
      console.log('[LivePulse] Connected')
      setStatus('connected')
    }

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        
        switch (payload.type) {
            case 'connected':
                // Initial connection success
                break
            case 'pong':
                // Heartbeat response
                break
            case 'new_item':
                if (onNewItem) onNewItem(payload.data)
                // Also update react-query cache cautiously
                queryClient.setQueryData(['pulse-feed', domainId], (oldData: PulsePaper[] | undefined) => {
                    if (!oldData) return [payload.data]
                    // Avoid duplicates
                    if (oldData.some(p => p.id === payload.data.id)) return oldData
                    return [payload.data, ...oldData]
                })
                break
            case 'breaking':
                if (onBreakingAlert) onBreakingAlert(payload.data)
                toast.error(`BREAKING: ${payload.data.title}`, {
                    duration: 5000,
                    icon: '⚡'
                })
                break
            case 'updated':
                // Handle item updates (e.g. freshness score change)
                queryClient.setQueryData(['pulse-feed', domainId], (oldData: PulsePaper[] | undefined) => {
                    if (!oldData) return oldData
                    return oldData.map(p => p.id === payload.data.id ? { ...p, ...payload.data } : p)
                })
                break
        }
      } catch (err) {
        console.error('[LivePulse] Message error:', err)
      }
    }

    ws.onclose = () => {
      console.log('[LivePulse] Disconnected')
      setStatus('disconnected')
      wsRef.current = null
      
      // Auto reconnect
      if (active) {
        reconnectTimeoutRef.current = setTimeout(connect, 3000)
      }
    }

    ws.onerror = (error) => {
      console.error('[LivePulse] Error:', error)
      setStatus('error')
      ws.close()
    }

    wsRef.current = ws
  }, [active, getWebSocketUrl, domainId, onNewItem, onBreakingAlert, queryClient])

  useEffect(() => {
    if (active) {
      connect()
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [active, connect])

  // Heartbeat to keep connection alive
  useEffect(() => {
    if (!active || status !== 'connected') return

    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [active, status])

  return { status }
}
