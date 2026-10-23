import { Link } from "react-router-dom"
import { PageHeader } from "../components/PageHeader"

export function About() {
  return (
    <div className="page narrow">
      <PageHeader
        eyebrow="Sobre"
        title="O que este protótipo faz"
        lede="É a interface do GameCompass antes da API. O cálculo acontece no navegador para o fluxo poder ser demonstrado."
      />
      <div className="prose">
        <p>
          Você cria uma conta, marca gêneros e temáticas, escolhe três jogos âncora e informa o computador. A lista
          resultante ordena por afinidade e esconde o que não roda na máquina.
        </p>
        <h2>Afinidade</h2>
        <p>
          A nota de 0 a 100 mistura o quanto o jogo compartilha gêneros e temáticas com o seu perfil e com os três
          jogos âncora. Estúdio em comum soma um pouco. Os âncoras não voltam na lista. Abaixo de 20, o título nem
          entra na disputa.
        </p>
        <h2>Hardware</h2>
        <p>
          Cada peça da base tem uma pontuação ilustrativa. O jogo entra se o processador, a placa, a memória e o
          sistema alcançam o mínimo daquele título. Não há chute: ou atende, ou fica na seção “fora do seu computador”.
        </p>
        <h2>O que ainda não existe</h2>
        <p>
          Não há FastAPI, Neo4j nem base real da Steam nesta tela. As pontuações não são benchmarks publicados. Quando
          o backend existir, estas páginas passam a chamar a API no lugar das funções locais.
        </p>
        <p>
          <Link to="/app">Voltar ao painel</Link>
        </p>
      </div>
    </div>
  )
}
