import { useState, useEffect } from 'react'
import { Landing } from './components/Landing'
import { Docs } from './components/Docs'

type Page = 'landing' | 'docs'

function getPageFromPath(): Page {
  return window.location.pathname === '/docs' ? 'docs' : 'landing'
}

export default function App() {
  const [page, setPage] = useState<Page>(getPageFromPath)

  useEffect(() => {
    const onPop = () => setPage(getPageFromPath())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  const navigate = (p: Page) => {
    const path = p === 'docs' ? '/docs' : '/'
    history.pushState(null, '', path)
    setPage(p)
  }

  if (page === 'docs') {
    return <Docs onBack={() => navigate('landing')} />
  }
  return <Landing onDocs={() => navigate('docs')} />
}
