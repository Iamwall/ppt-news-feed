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

// Configuration for reconnection strategy
const MAX_RETRIES = 5
const INITIAL_DELAY_MS = 1000
const MAX_DELAY_MS = 30000

export function useLiveFeed({ domainId, active = true, onNewItem, onBreakingAlert }: UseLiveFeedOptions) {
  const [status, setStatus] = useState<WebSocketStatus>('disconnected')
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()
  const retryCountRef = useRef(0)
  const isConnectingRef = useRef(false) // Guard against duplicate connections
  const queryClient = useQueryClient()

  // Construct WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = 'localhost:8000'
    const path = '/api/v1/'
    const wsEndpoint = domainId ? `ws/pulse/${domainId}` : 'ws/pulse'
    return `${protocol}//${host}${path}${wsEndpoint}`
  }, [domainId])

  // Calculate delay with exponential backoff
  const getReconnectDelay = useCallback(() => {
    const delay = Math.min(INITIAL_DELAY_MS * Math.pow(2, retryCountRef.current), MAX_DELAY_MS)
    return delay + Math.random() * 1000 // Add jitter
  }, [])

  const connect = useCallback(() => {
    // Guard: Don't create new connection if one is in progress or already open
    if (!active || isConnectingRef.current) {
      return
    }
    
    // Guard: Close any existing connection first
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
        console.log('[LivePulse] Closing existing connection before reconnect')
        wsRef.current.close()
        wsRef.current = null
      }
    }

    // Guard: Check max retries
    if (retryCountRef.current >= MAX_RETRIES) {
      console.log(`[LivePulse] Max retries (${MAX_RETRIES}) reached. Giving up.`)
      setStatus('error')
      return
    }

    const url = getWebSocketUrl()
    console.log(`[LivePulse] Connecting to: ${url} (attempt ${retryCountRef.current + 1}/${MAX_RETRIES})`)
    
    isConnectingRef.current = true
    setStatus('connecting')
    
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('[LivePulse] Connected successfully!')
        isConnectingRef.current = false
        retryCountRef.current = 0 // Reset retry count on success
        setStatus('connected')
      }

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data)
          
          switch (payload.type) {
            case 'connected':
              console.log('[LivePulse] Received connection confirmation')
              break
            case 'pong':
              // Heartbeat response - silent
              break
            case 'new_item':
              if (onNewItem) onNewItem(payload.data)
              queryClient.setQueryData(['pulse-feed', domainId], (oldData: PulsePaper[] | undefined) => {
                if (!oldData) return [payload.data]
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
              queryClient.setQueryData(['pulse-feed', domainId], (oldData: PulsePaper[] | undefined) => {
                if (!oldData) return oldData
                return oldData.map(p => p.id === payload.data.id ? { ...p, ...payload.data } : p)
              })
              break
          }
        } catch (err) {
          console.error('[LivePulse] Message parse error:', err)
        }
      }

      ws.onclose = (event) => {
        console.log(`[LivePulse] Disconnected (code: ${event.code}, reason: ${event.reason || 'none'})`)
        isConnectingRef.current = false
        wsRef.current = null
        setStatus('disconnected')
        
        // Auto-reconnect with exponential backoff (only if still active)
        if (active && retryCountRef.current < MAX_RETRIES) {
          retryCountRef.current++
          const delay = getReconnectDelay()
          console.log(`[LivePulse] Reconnecting in ${Math.round(delay / 1000)}s...`)
          reconnectTimeoutRef.current = setTimeout(connect, delay)
        }
      }

      ws.onerror = () => {
        // Error handler - the close handler will be called next
        // Don't set error status here, let onclose handle reconnection
        console.warn('[LivePulse] Connection error occurred')
      }

    } catch (err) {
      console.error('[LivePulse] Failed to create WebSocket:', err)
      isConnectingRef.current = false
      setStatus('error')
    }
  }, [active, getWebSocketUrl, getReconnectDelay, domainId, onNewItem, onBreakingAlert, queryClient])

  // Main effect: connect/disconnect based on active state
  useEffect(() => {
    if (active) {
      retryCountRef.current = 0 // Reset retries when activating
      connect()
    }

    return () => {
      // Cleanup: close connection and clear timers
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = undefined
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      isConnectingRef.current = false
    }
  }, [active]) // Intentionally NOT including connect to avoid infinite loop

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

  // Manual retry function for UI
  const retry = useCallback(() => {
    retryCountRef.current = 0
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    connect()
  }, [connect])

  return { status, retry }
}
