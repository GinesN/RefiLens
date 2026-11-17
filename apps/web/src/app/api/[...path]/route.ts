import { NextRequest } from "next/server";

const allowed =
  /^(companies(?:\/\d+(?:\/(?:financials|debt-maturities|data-quality|evidence|research-brief|financial-review|stress-defaults|case-study))?)?|peer-comparison|scenarios\/calculate|liquidity\/calculate|stress-tests\/calculate)$/;

async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const endpoint = path.join("/");
  if (
    !allowed.test(endpoint) ||
    (request.method === "POST" &&
      ![
        "scenarios/calculate",
        "liquidity/calculate",
        "stress-tests/calculate",
      ].includes(endpoint))
  ) {
    return Response.json({ detail: "Endpoint not allowed." }, { status: 404 });
  }
  const isPost = request.method === "POST";
  const body = isPost ? await request.text() : undefined;
  if (body && body.length > 16_384)
    return Response.json({ detail: "Request too large." }, { status: 413 });
  try {
    const response = await fetch(
      `${process.env.API_BASE_URL || "http://127.0.0.1:8000"}/api/${endpoint}${request.nextUrl.search}`,
      {
        method: request.method,
        headers: { "Content-Type": "application/json" },
        body,
        cache: "no-store",
        signal: AbortSignal.timeout(10_000),
      },
    );
    return new Response(await response.text(), {
      status: response.status,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return Response.json(
      {
        detail:
          "Research API unavailable. Start the backend with ./scripts/dev.sh.",
      },
      { status: 503 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
