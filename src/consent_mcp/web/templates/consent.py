"""HTML templates for consent pages."""


from consent_mcp.domain.value_objects import ConsentStatus


def render_consent_page(
    token: str,
    requester_name: str,
    scope: str,
    target_name: str | None = None,
) -> str:
    """Render the consent confirmation page."""
    greeting = f"Hi {target_name}" if target_name else "Hello"

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Consent Request</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .card {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 480px;
                width: 100%;
                padding: 40px;
            }}
            h1 {{
                color: #333;
                font-size: 24px;
                margin-bottom: 20px;
            }}
            .greeting {{
                color: #666;
                font-size: 16px;
                margin-bottom: 24px;
            }}
            .scope-box {{
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 16px;
                border-radius: 0 8px 8px 0;
                margin: 24px 0;
            }}
            .scope-label {{
                font-size: 12px;
                color: #999;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .scope-text {{
                font-size: 18px;
                color: #333;
                margin-top: 8px;
            }}
            .buttons {{
                display: flex;
                gap: 12px;
                margin-top: 32px;
            }}
            button {{
                flex: 1;
                padding: 14px 24px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            button:hover {{
                transform: translateY(-2px);
            }}
            .grant {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }}
            .deny {{
                background: #f1f3f4;
                color: #666;
            }}
            .notice {{
                margin-top: 24px;
                font-size: 12px;
                color: #999;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🔐 Consent Request</h1>
            <p class="greeting">{greeting},</p>
            <p><strong>{requester_name}</strong> is requesting your permission for an AI agent to contact you.</p>

            <div class="scope-box">
                <div class="scope-label">Purpose</div>
                <div class="scope-text">{scope}</div>
            </div>

            <p>By clicking <strong>Grant Consent</strong>, you authorize this request.</p>

            <div class="buttons">
                <form action="/v1/consent/{token}/grant" method="post" style="flex: 1;">
                    <button type="submit" class="grant" style="width: 100%;">Grant Consent</button>
                </form>
                <form action="/v1/consent/{token}/deny" method="post" style="flex: 1;">
                    <button type="submit" class="deny" style="width: 100%;">Decline</button>
                </form>
            </div>

            <p class="notice">
                This is a one-time consent request. You can revoke consent at any time.
            </p>
        </div>
    </body>
    </html>
    """


def render_thank_you(granted: bool) -> str:
    """Render the thank you page after response."""
    if granted:
        icon = "✅"
        title = "Consent Granted"
        message = "Thank you! Your consent has been recorded."
        color = "#10b981"
    else:
        icon = "❌"
        title = "Consent Declined"
        message = "You have declined this consent request."
        color = "#ef4444"

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .card {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 400px;
                width: 100%;
                padding: 40px;
                text-align: center;
            }}
            .icon {{
                font-size: 64px;
                margin-bottom: 20px;
            }}
            h1 {{
                color: {color};
                font-size: 24px;
                margin-bottom: 16px;
            }}
            p {{
                color: #666;
                font-size: 16px;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">{icon}</div>
            <h1>{title}</h1>
            <p>{message}</p>
        </div>
    </body>
    </html>
    """


def render_already_responded(status: ConsentStatus) -> str:
    """Render page for already-responded requests."""
    status_text = status.value.title()
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Already Responded</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .card {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 400px;
                width: 100%;
                padding: 40px;
                text-align: center;
            }}
            .icon {{
                font-size: 64px;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #666;
                font-size: 24px;
                margin-bottom: 16px;
            }}
            p {{
                color: #999;
                font-size: 16px;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">ℹ️</div>
            <h1>Already Responded</h1>
            <p>This consent request has already been {status_text.lower()}.</p>
        </div>
    </body>
    </html>
    """
