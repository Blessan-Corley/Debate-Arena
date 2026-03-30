const rawBase = import.meta.env.VITE_API_BASE_URL?.trim() || ''


export function apiUrl(path) {
  const base = rawBase.endsWith('/') ? rawBase.slice(0, -1) : rawBase
  return base ? `${base}${path}` : path
}


export function networkErrorMessage(path) {
  return `Cannot reach the backend at ${apiUrl(path)}. Make sure the FastAPI server is running.`
}


export async function apiJson(path, options = {}) {
  let response
  try {
    response = await fetch(apiUrl(path), {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    })
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(networkErrorMessage(path))
    }
    throw error
  }

  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const detail = typeof data === 'object' && data ? data.detail || data.message : data
    throw new Error(detail || 'Request failed')
  }

  return data
}
