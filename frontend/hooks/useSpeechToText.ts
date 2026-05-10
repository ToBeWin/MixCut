'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

type SpeechRecognitionInstance = {
  continuous: boolean
  interimResults: boolean
  lang: string
  onresult: ((event: SpeechRecognitionEventLike) => void) | null
  onend: (() => void) | null
  onerror: ((event: { error: string }) => void) | null
  start: () => void
  stop: () => void
}

type SpeechRecognitionEventLike = {
  results: ArrayLike<{
    isFinal: boolean
    0: { transcript: string }
  }>
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor
    webkitSpeechRecognition?: SpeechRecognitionConstructor
  }
}

export function useSpeechToText(language: string, onTranscript: (transcript: string) => void) {
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)
  const [isSupported, setIsSupported] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognitionCtor) {
      setIsSupported(false)
      recognitionRef.current = null
      return
    }

    const recognition = new SpeechRecognitionCtor()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = language

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join(' ')
        .trim()
      if (transcript) onTranscript(transcript)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.onerror = (event) => {
      setError(event.error)
      setIsListening(false)
    }

    recognitionRef.current = recognition
    setIsSupported(true)

    return () => {
      recognition.stop()
      recognitionRef.current = null
    }
  }, [language, onTranscript])

  const startListening = useCallback(() => {
    const recognition = recognitionRef.current
    if (!recognition) return
    setError(null)
    setIsListening(true)
    recognition.start()
  }, [])

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop()
    setIsListening(false)
  }, [])

  return { isSupported, isListening, error, startListening, stopListening }
}
