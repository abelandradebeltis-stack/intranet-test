
from app import create_app, db
from app.models import Client

def seed_clients():
    """Seeds the database with initial client data."""
    app = create_app()
    with app.app_context():
        # Check if clients already exist
        if Client.query.count() > 0:
            print("Clients already seeded.")
            return

        clients = [
            Client(
                name="Cliente 1",
                logo="https://via.placeholder.com/150",
                status="Ativo",
                panel_url="https://www.google.com",
                wiki_url="https://www.google.com"
            ),
            Client(
                name="Cliente 2",
                logo="https://via.placeholder.com/150",
                status="Inativo",
                panel_url="https://www.google.com",
                wiki_url="https://www.google.com"
            ),
            Client(
                name="Cliente 3",
                logo="https://via.placeholder.com/150",
                status="Ativo",
                panel_url="https://www.google.com",
                wiki_url="https://www.google.com"
            )
        ]

        db.session.bulk_save_objects(clients)
        db.session.commit()
        print("Clients seeded successfully.")

if __name__ == "__main__":
    seed_clients()
