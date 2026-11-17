# RefiLens: guía fácil de uso

RefiLens ayuda a contestar una pregunta: **si una empresa tiene que devolver deuda, ¿de dónde podría sacar el dinero y qué ocurre si las condiciones empeoran?** Parte de datos reales de informes oficiales y permite hacer simulaciones. No predice quiebras ni recomienda comprar acciones.

## Abrir la aplicación

- Página inicial: http://localhost:3000
- Caso financiero terminado: http://localhost:3000/?company=NUE#case-study
- Simulador de escenarios: http://localhost:3000/?company=NUE#stress

Estos enlaces funcionan en el Mac donde se está ejecutando RefiLens. Todavía no son una web pública para compartir con un reclutador. Si no carga, abre `Start RefiLens.command` en la carpeta del proyecto. La Terminal es el motor que mantiene la aplicación funcionando: no necesitas escribir nada. Puedes minimizarla; si paras ese motor, la página deja de responder.

## Antes de interpretar los números

La aplicación está en inglés. **M** significa millones y **B** significa mil millones; el inglés “billion” no equivale al billón español. `$2.26B` son 2.260 millones de dólares. El punto en la pantalla separa decimales, no miles.

Los datos son del ejercicio 2025, con cierre el 31 de diciembre de 2025. “Live SEC import” significa que se importaron de la SEC; no significa que sean los saldos de hoy. “Offline filing snapshot” es una copia auténtica guardada para trabajar sin volver a descargarla. La SEC es el organismo estadounidense donde las empresas presentan sus informes.

Un **dato histórico** dice qué declaró la empresa. Un **supuesto** dice qué estamos imaginando para hacer una prueba. Cambiar un interés futuro no cambia las cuentas históricas.

## La nueva portada: Project introduction

La página inicial explica la pregunta del proyecto y enseña un resultado del caso de Nucor. **Explore the Nucor case** abre el análisis desarrollado; **Open research workspace** abre el resumen financiero. El recorrido de tres pasos lleva a las fuentes, el caso y los simuladores.

Ahora puedes descargar dos PDF directamente: **Project brief** presenta el proyecto en dos páginas y **Nucor case** desarrolla el análisis en cuatro. **Download presentation pack** reúne esos documentos, el JSON, el memo, las instrucciones y las limitaciones en un ZIP. No necesitas poner el programa en marcha para leer sus documentos una vez descargados. Los PDF no equivalen a una revisión personal tuya.

Los botones Atrás y Adelante del navegador conservan la pantalla y la empresa del recorrido. Cambiar de empresa sigue reiniciando sus borradores para evitar mezclas.

## Qué hace cada pantalla

### 1. Company selector y Companies

El selector de arriba cambia de empresa. También puedes entrar en **Companies**, buscar por nombre o ticker y abrir una ficha. Los tickers disponibles son NUE (Nucor), STLD (Steel Dynamics), RS (Reliance), LECO (Lincoln Electric) e ITW (Illinois Tool Works).

Las cinco tienen los campos compatibles que necesita este análisis. Nucor y Steel Dynamics producen acero; Reliance distribuye metales; Lincoln Electric fabrica equipos y consumibles de soldadura; ITW es un grupo industrial diversificado con un negocio de soldadura. En ITW se analiza el grupo entero, no solo la soldadura. No se afirma que sean negocios idénticos. Al cambiar de empresa se borran los borradores de simulación de la empresa anterior para evitar mezclarlos.

### 2. Overview: el resumen de una empresa

Muestra qué deuda vence próximamente y cuatro cifras principales:

- **Gross financial debt:** deuda contabilizada según la definición indicada. No es necesariamente el mismo importe que el principal de los préstamos.
- **Cash & equivalents:** efectivo y equivalentes declarados. No se supone que todo esté libremente disponible para la matriz.
- **Net debt:** deuda menos el efectivo elegible. Permite ver la deuda después de descontar esa caja; no significa que la empresa vaya a gastarla toda.
- **Gross interest expense:** gasto por intereses declarado. No equivale automáticamente al efectivo pagado ni se sustituye por intereses netos.

Pulsar una cifra abre su origen, fórmula y advertencias. **View financial details** amplía la información, incluyendo generación de caja y medidas de cobertura.

Debajo hay un gráfico de vencimientos y un simulador pequeño de intereses. **Compare stress scenarios** abre el análisis de caja con varios escenarios. **Inspect debt maturities** abre el calendario de devolución.

### 3. Debt maturities: cuándo hay que devolver el principal

Las barras muestran importes que la empresa declaró para años concretos. Una barra alta significa más principal que devolver en ese año; no es una probabilidad de impago.

**Thereafter** significa “después de los años detallados”. Se muestra aparte porque no sabemos cómo repartirlo. RefiLens no inventa que todo vence en un año concreto. Un cero declarado se conserva; un dato que falta no se convierte en cero.

El principal es lo que se debe devolver. El valor contable puede ser diferente por costes de emisión, descuentos, primas o arrendamientos. El apartado de revisión explica esas diferencias.

### 4. Scenario analysis: tres herramientas distintas

**Stress scenarios** compara Base, Adverse y Severe. Son puntos de partida editables, no pronósticos oficiales. Cada uno puede tener una reducción de caja operativa, inversión, tipo de interés, porcentaje refinanciado y comisión distintos.

- **Edit case assumptions:** abre los valores de los tres escenarios.
- **Shared cash settings and other outflows:** cambia caja inicial, reserva deseada, interés antiguo supuesto, años y otros pagos.
- **Base / Adverse / Severe:** selecciona qué resultado inspeccionar.
- **Ending cash:** cuánto dinero quedaría según los supuestos, antes de conseguir financiación adicional.
- **Peak shortfall:** el mayor importe que faltaría para mantener la reserva elegida. No suma varias veces el mismo déficit.
- **First shortfall year:** primer cierre anual por debajo de esa reserva.
- **Cash curves:** compara la trayectoria anual de los tres casos.
- **Why cash changes versus Base:** separa el efecto de operaciones, inversión, refinanciación, comisiones e intereses.
- **Rate and cash-flow sensitivity:** cada casilla prueba otra combinación de intereses y caja operativa. Mantiene fijos los demás supuestos del escenario seleccionado. “Unavailable” significa que esa combinación no es coherente con los límites del modelo; no significa que falte cero dinero.
- **Explore … year by year:** lleva exactamente ese caso al modelo anual.
- **Export stress cases JSON:** descarga todos los valores, resultados y referencias para poder reproducir la prueba.
- **Reset stress assumptions:** recupera los valores iniciales; está dentro del editor.

**Annual cash model** es la herramienta detallada. Permite introducir por año la caja generada por el negocio, la inversión y otros pagos, y seguir la suma de entradas y salidas. No inserta un préstamo imaginario para arreglar un resultado negativo.

**Single maturity** aísla un vencimiento. Sirve para preguntar: “si refinancio este importe a un interés diferente, ¿cuánto cambia el gasto anual por intereses y su cobertura?”. También permite estresar los beneficios de referencia. No calcula por sí solo toda la caja futura. Un EBITDA introducido manualmente sigue siendo una hipótesis, porque no tenemos uno observado y conciliado.

Los borradores se conservan al cambiar de herramienta dentro de la misma empresa, pero no son una biblioteca guardada: al recargar la página se reinician. Si introduces un valor inválido, desaparece el resultado anterior para no exportar por error una simulación antigua.

### 5. Case study: el caso financiero completo de Nucor

La pregunta es si, durante 2026–2027, puede financiar vencimientos, inversión y repartos de dinero si empeora la caja del negocio. Es un ejercicio histórico basado en el informe presentado el 25 de febrero de 2026, no una evaluación de su situación actual.

Compara cuatro casos:

1. Repetir la generación de caja de 2025 y ciertas salidas de dinero, usando como referencia la estimación de inversión para 2026.
2. Aplicar otra caída de caja operativa de la misma magnitud absoluta que se observó entre 2024 y 2025.
3. Añadir refinanciación más limitada, otro interés y comisiones supuestas.
4. Mantener esa presión y eliminar únicamente las recompras de acciones.

Una **recompra** es dinero que una empresa utiliza para comprar sus propias acciones. No es lo mismo que pagar una deuda o un dividendo.

En el ejercicio, pausar las recompras conserva 1.400 millones de dólares durante dos años. La caja final pasa a ser positiva, unos 363 millones, pero sigue por debajo de la reserva de 500 millones elegida como supuesto. Faltarían aproximadamente 137 millones para esa reserva. Una mejora adicional de caja de unos 68,6 millones en CADA uno de los dos años la alcanzaría matemáticamente, si todo lo demás se mantiene igual. La aplicación no afirma que obtener esa mejora sea fácil o posible.

El caso incluye dividendos, distribuciones a socios minoritarios y ciertos pagos fiscales ligados a acciones. Sus importes históricos se repiten como hipótesis, no como obligaciones futuras. Conserva todos ellos cuando pausa las recompras. La capacidad de la línea de crédito se muestra como contexto, pero no se añade automáticamente a la caja.

**Download case PDF** descarga el caso maquetado. **Review** cambia el caso que muestra el detalle anual. **Open selected case in annual model** permite experimentar con sus importes exactos. **Download case memo** descarga el informe escrito en un archivo de texto Markdown; **Export case JSON** descarga las cifras y referencias. **Source appendix** enseña qué es histórico, qué era una estimación de la dirección y qué era capacidad de crédito.

Este caso y los escenarios generales parten de horizontes y supuestos distintos. Por eso sus resultados pueden ser diferentes sin que haya un error.

### 6. Peer comparison: comparar con las otras empresas

Coloca las cinco empresas en una tabla con datos comparables y sus definiciones. Ajusta expresamente el tratamiento de los arrendamientos financieros de Nucor para la comparación. La ficha individual conserva su definición original.

Permite observar diferencias de deuda, caja, vencimientos y flujos. No presenta un ranking de “mejor empresa” ni afirma que sus riesgos sean equivalentes. Puedes abrir otra ficha o exportar la comparación.

### 7. Research brief: una nota breve

Resume la empresa seleccionada mediante una plantilla y añade sus fuentes. Es una ficha rápida; **Case study** es el análisis desarrollado con una pregunta y varios casos.

**Print / save PDF** usa la ventana de impresión del navegador. Puedes elegir guardar como PDF desde esa ventana. No hace falta una cuenta ni pagar un servicio.

### 8. Filings & evidence: comprobar el origen

Aquí se ven el informe original, las referencias, los controles de extracción y las advertencias. **Cross-checked** significa que coinciden dos representaciones del mismo informe, no que un auditor independiente garantice la cifra. **Source-extracted** significa que se extrajo de una fuente sin esa segunda coincidencia. Ninguna etiqueta afirma revisión humana.

**Financial review** enseña cómo se llega desde las notas de deuda al valor contable, las diferencias de efectivo restringido y los redondeos. Puedes descargar su JSON o el Excel de revisión. El Excel contiene fórmulas y campos de revisión personal vacíos: descargarlo no significa que tú ya hayas revisado las cuentas.

### 9. Methodology: las reglas del cálculo

Explica qué incluye cada cifra, las fórmulas y lo que queda fuera. Es el lugar para resolver dudas sobre deuda neta, FCF, intereses, periodos, monedas, vencimientos y supuestos. También ayuda a preparar una entrevista: necesitas poder explicar por qué una cifra se calcula así y dónde deja de ser útil.

## Diccionario de los controles del modelo anual

| Etiqueta | En palabras sencillas |
|---|---|
| Available opening cash | Dinero con el que suponemos que empieza la simulación. |
| Minimum cash floor | Reserva que queremos conservar. No es automáticamente un requisito legal o bancario. |
| Operating cash flow / CFO | Dinero generado o consumido por las operaciones, antes del cambio de intereses que calcula el modelo. No es el beneficio contable. |
| Cash capex | Dinero invertido en instalaciones, equipos u otros activos incluidos en la definición. |
| Other cash uses | Otros pagos: dividendos, recompras, adquisiciones, determinadas obligaciones, etc. Solo entran los que se han introducido. |
| Original / previous rate | Interés antiguo que suponemos para la deuda que vence. No afirma que sea su cupón real. |
| New borrowing rate | Interés que suponemos para la nueva deuda. |
| Principal refinanced | Qué parte del vencimiento suponemos que se sustituye por otro préstamo. El resto sale de caja. |
| Issuance fee | Comisión supuesta por emitir la nueva deuda. |
| Projection horizon | Cuántos años se calculan, dentro de los años exactos que sí tenemos. |
| Unfunded cash balance | Resultado antes de conseguir nueva financiación para tapar un agujero. Un negativo indica una necesidad pendiente, no un saldo bancario que se pueda mantener. |
| FCF | Caja operativa menos inversión de caja definida; no incluye automáticamente todas las demás salidas. |

## Recorrido recomendado de cinco minutos

1. Abre Nucor en Overview y pulsa la deuda para ver de dónde viene.
2. Mira los 598 millones de principal que vencen en 2026–2027 y la deuda que queda fuera de esos años.
3. Abre Case study y lee primero la pregunta y la conclusión.
4. Pulsa Review en los cuatro casos y observa qué cambia cada vez.
5. Abre el caso de pausa de recompras en el modelo anual: verás los mismos resultados y pagos.
6. Prueba otro supuesto y observa el efecto. Vuelve al caso original si quieres comparar.
7. Abre Filings & evidence y después el informe oficial.
8. Antes de usar el proyecto en una entrevista, completa tu revisión personal y explica las limitaciones con tus palabras.

## Particularidades de las dos nuevas empresas

**LECO:** sus préstamos bancarios ya están dentro del vencimiento de 2026. La simulación no vuelve a restarlos. El informe publica 6.000 USD para 2027: es una cifra pequeña real, no un hueco rellenado. El total del calendario es 4.000 USD menor que el de la nota de deuda; la diferencia cabe justo en el límite de precisión de las cifras publicadas, se muestra y no se reparte entre años.

**ITW:** los 1.287 millones USD de papel comercial (financiación a corto plazo) están fuera del calendario de deuda a largo plazo. La simulación parte del supuesto visible de devolverlos en 2026; puedes cambiarlo. El cero de 2029 sí está publicado en el informe.

Ambas tienen ficha, fuentes, revisión financiera, vencimientos, informe y los mismos simuladores y exportaciones. Los datos son de 2025; la caja futura que veas sigue siendo una simulación.
