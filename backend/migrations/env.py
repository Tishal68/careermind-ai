from alembic import context

# The application supplies an already configured connection, keeping credentials
# out of alembic.ini and preserving its connection/statement timeouts.
connection = context.config.attributes["connection"]
context.configure(connection=connection)
with context.begin_transaction():
    context.run_migrations()
