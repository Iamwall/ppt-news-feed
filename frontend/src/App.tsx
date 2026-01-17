import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Papers from './pages/Papers'
import Digests from './pages/Digests'
import DigestDetail from './pages/DigestDetail'
import Newsletters from './pages/Newsletters'
import NewsletterEditor from './pages/NewsletterEditor'
import Settings from './pages/Settings'
import Sources from './pages/Sources'
import Fetch from './pages/Fetch'
import { BrandingProvider } from './contexts/BrandingContext'

function App() {
  return (
    <BrandingProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="papers" element={<Papers />} />
          <Route path="fetch" element={<Fetch />} />
          <Route path="digests" element={<Digests />} />
          <Route path="digests/:id" element={<DigestDetail />} />
          <Route path="newsletters" element={<Newsletters />} />
          <Route path="newsletters/:id/edit" element={<NewsletterEditor />} />
          <Route path="sources" element={<Sources />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrandingProvider>
  )
}

export default App
