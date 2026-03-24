from playwright.async_api import async_playwright


async def iniciar_browser(HEADLESS_BOOL):
    """
    Inicializa Playwright y abre un navegador Chromium visible.

    Returns:
        tuple: (playwright, browser, context, page)
            playwright: instancia de Playwright.
            browser: navegador Chromium.
            context: contexto del navegador.
            page: página inicial.
    """
    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(
        headless=HEADLESS_BOOL,
        args=["--start-maximized"]
    )

    context = await browser.new_context(viewport=None)
    page = await context.new_page()

    # Optimización: Bloquear recursos pesados
    async def bloquear_recursos(route):
        if route.request.resource_type in ["image", "font", "media"]:
            await route.abort()
        else:
            await route.continue_()

    await page.route("**/*", bloquear_recursos)

    return playwright, browser, context, page


async def cerrar_browser(playwright, browser) -> None:
    """
    Cierra el navegador y detiene Playwright.

    Args:
        playwright: Instancia activa de Playwright.
        browser: Instancia del navegador.

    Returns:
        None
    """
    await browser.close()
    await playwright.stop()
