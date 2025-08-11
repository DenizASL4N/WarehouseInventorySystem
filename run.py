from app import create_app, db

app = create_app()

@app.shell_context_processor
def make_shell_context():
    # Modelleriniz tanımlandıktan sonra buraya eklenecek
    # from app.models import User, Product # Örnek
    # return {'db': db, 'User': User, 'Product': Product}
    return {'db': db}

if __name__ == '__main__':
    app.run()