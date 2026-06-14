import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const cubeApiUrl =
  import.meta.env.VITE_CUBE_API_URL ?? "http://localhost:4000/cubejs-api/v1";

function App() {
  return (
    <main className="shell">
      <section className="card">
        <p className="eyebrow">Industrial Analytics Platform</p>
        <h1>Le socle technique est prêt.</h1>
        <p>
          React, Vite, Cube, PostgreSQL et le service d'import Python sont
          connectés. L'interface métier viendra dans une prochaine étape.
        </p>
        <dl>
          <div>
            <dt>Cube API</dt>
            <dd>{cubeApiUrl}</dd>
          </div>
          <div>
            <dt>État</dt>
            <dd>Environnement de développement</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
