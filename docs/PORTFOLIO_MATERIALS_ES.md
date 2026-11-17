# Material de presentación de RefiLens

Los siguientes textos describen funciones verificables del proyecto. No afirman que el propietario haya programado todos sus componentes o revisado personalmente las cuentas. Antes de atribuirte una contribución concreta, identifica lo que realmente hiciste y puedes explicar.

## Descripción breve del proyecto

RefiLens es un proyecto de análisis de deuda corporativa que conecta informes oficiales de la SEC con vencimientos de deuda y simulaciones transparentes de caja. Incluye cinco empresas con datos anuales de 2025, cálculos financieros en Python Decimal y un caso de Nucor que compara inversión, repartos de efectivo y refinanciación.

## Texto de presentación para LinkedIn — borrador, no publicado

RefiLens parte de una pregunta financiera concreta: ¿puede una empresa mostrar una buena cobertura de intereses y, aun así, tener una necesidad de caja?

El proyecto conecta datos de informes oficiales con un calendario de vencimientos, un modelo anual de caja y escenarios editables. Cada resultado conserva sus fuentes y separa las cifras históricas de las hipótesis.

El caso de Nucor muestra esa diferencia: bajo unos supuestos explícitos de presión operativa y refinanciación, pausar recompras conservaría caja, pero no bastaría para alcanzar la reserva elegida. La simulación cuantifica lo que aún faltaría sin inventar financiación para resolverlo.

Los datos son históricos; el modelo no produce calificaciones crediticias ni probabilidades de impago. La revisión personal de fuentes es una tarea separada y no se da por realizada.

## Descripción factual para la sección de proyectos del CV

**RefiLens — análisis de deuda corporativa y escenarios de liquidez.** Proyecto con Next.js/TypeScript, FastAPI, Python Decimal y evidencia de informes SEC. Incluye cinco emisores FY2025/USD, trazabilidad de deuda y vencimientos, escenarios reproducibles y un caso financiero documentado de Nucor. Contribución personal: describir únicamente la parte efectivamente realizada y comprendida; el proyecto no atribuye trabajo personal no verificado.

## Demostración de tres minutos

1. **0:00–0:25 — Problema.** “RefiLens estudia si la caja puede cubrir un plan financiero, aunque la cuenta de resultados muestre cobertura de intereses.”
2. **0:25–0:55 — Evidencia.** Abre el informe de Nucor y señala cierre fiscal, fecha de presentación, caja, inversión y vencimientos. Explica por qué un dato histórico no es el saldo de hoy.
3. **0:55–1:40 — Caso.** Compara los cuatro casos. La respuesta de pausa de recompras conserva dividendos, pagos a socios minoritarios y retenciones fiscales. Aclara que las repeticiones futuras y los términos de financiación son hipótesis.
4. **1:40–2:20 — Cálculo.** Abre la respuesta en el modelo anual. Distingue saldo de caja positivo de una reserva insuficiente. Cambia un supuesto y observa cómo se modifica el resultado.
5. **2:20–3:00 — Límites y reproducción.** Descarga el JSON y el PDF. Explica el periodo del caso, la falta de un EBITDA conciliado, la no asignación de Thereafter y la revisión humana pendiente.

## Ocho preguntas que debes poder responder

- ¿Por qué beneficio contable y caja no son lo mismo?
- ¿Por qué se compara la caja de un momento con flujos de un periodo?
- ¿Qué salidas de dinero quedan después de calcular CFO menos capex?
- ¿Qué cambia entre las definiciones de deuda contable y principal contractual?
- ¿Por qué los intereses históricos no se vuelven a restar completos del CFO?
- ¿Cómo afecta refinanciar solo una parte del vencimiento a caja e intereses?
- ¿Por qué un saldo positivo todavía puede incumplir una reserva elegida?
- ¿Qué datos y condiciones faltan para convertir una simulación en un plan de financiación real?

La respuesta debe ser tuya y basarse en lo que entiendes. OWNER_VERIFICATION_CHECKLIST.md conserva los campos de revisión personal vacíos. Este material no equivale a esa revisión ni publica mensajes por ti.
