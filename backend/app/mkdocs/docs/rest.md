<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <link href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" rel="stylesheet" />

     <!-- <link rel="shortcut icon" href="{swagger_favicon_url}"> -->
</head>
<body>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.7.2/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {
        const ui = SwaggerUIBundle({
            url: "/openapi.json",
            dom_id: '#swagger',
            layout: 'BaseLayout',
            deepLinking: true,
            presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIBundle.SwaggerUIStandalonePreset
            ]
        })

        window.ui = ui
        }
    </script>

    <div id="swagger"></div>
</body>
</html>