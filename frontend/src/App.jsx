import { useState, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

const API_BASE = 'http://localhost:8000'

function App() {
  const [url, setUrl] = useState('')
  const [taskId, setTaskId] = useState(null)
  const [status, setStatus] = useState('')
  const [result, setResult] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Функция отправки URL
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!url.trim()) {
      setError('Введите URL')
      return
    }

    setLoading(true)
    setError('')
    setResult('')
    setStatus('Отправка запроса...')

    try {
      const response = await axios.post(`${API_BASE}/submit`, { url })
      setTaskId(response.data.task_id)
      setStatus('Обработка...')
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка отправки запроса')
      setLoading(false)
    }
  }

  // Поллинг статуса задачи
  useEffect(() => {
    if (!taskId) return

    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE}/status/${taskId}`)
        const data = response.data

        if (data.status === 'completed') {
          setResult(data.result)
          setStatus('Готово!')
          setLoading(false)
          setTaskId(null)
          clearInterval(pollInterval)
        } else if (data.status === 'failed') {
          setError(data.error || 'Ошибка обработки')
          setLoading(false)
          setTaskId(null)
          clearInterval(pollInterval)
        } else {
          setStatus('Обработка... (это может занять до минуты)')
        }
      } catch (err) {
        setError('Ошибка получения статуса')
        setLoading(false)
        setTaskId(null)
        clearInterval(pollInterval)
      }
    }, 2000) // Опрос каждые 2 секунды

    return () => clearInterval(pollInterval)
  }, [taskId])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Заголовок */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-gray-800 mb-3">
            🤖 AI-Summary
          </h1>
          <p className="text-gray-600 text-lg">
            Умные выжимки из YouTube и веб-страниц
          </p>
        </div>

        {/* Форма ввода */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-gray-700 font-semibold mb-2">
                Вставьте ссылку на YouTube видео или веб-страницу:
              </label>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://youtube.com/watch?v=... или https://example.com/article"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-indigo-500 transition"
                disabled={loading}
              />
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-3 rounded-lg font-semibold text-white transition ${
                loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-700 active:scale-95'
              }`}
            >
              {loading ? '⏳ Обработка...' : '✨ Создать выжимку'}
            </button>
          </form>

          {/* Статус */}
          {status && !error && (
            <div className="mt-4 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
              <p className="text-blue-700 font-medium">{status}</p>
            </div>
          )}

          {/* Ошибка */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-500 rounded">
              <p className="text-red-700 font-medium">❌ {error}</p>
            </div>
          )}
        </div>

        {/* Результат */}
        {result && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
              📝 Выжимка
            </h2>
            <div className="prose prose-lg max-w-none">
              <ReactMarkdown
                className="text-gray-700 leading-relaxed"
                components={{
                  p: ({ children }) => <p className="mb-4">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc ml-6 mb-4">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal ml-6 mb-4">{children}</ol>,
                  h1: ({ children }) => <h1 className="text-2xl font-bold mb-3">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-xl font-bold mb-2">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-lg font-semibold mb-2">{children}</h3>,
                }}
              >
                {result}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App