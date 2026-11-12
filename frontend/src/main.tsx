import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { BrowserRouter } from "react-router-dom"
import { App } from "./App"
import { SessionProvider } from "./context/SessionContext"
import { CatalogProvider } from "./context/CatalogContext"
import { SoundProvider } from "./context/SoundContext"
import "./styles/global.css"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <SoundProvider>
        <SessionProvider>
          <CatalogProvider>
            <App />
          </CatalogProvider>
        </SessionProvider>
      </SoundProvider>
    </BrowserRouter>
  </StrictMode>,
)
