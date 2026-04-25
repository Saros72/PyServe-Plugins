def register(app):
    @app.route("/hello_world")
    def hello_world_route():
        return "<h1 style='text-align:center;margin-top:20px;'>Hello World 👍</h1>"