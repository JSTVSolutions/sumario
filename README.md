# sumario

## Quick start

* Install [Podman](https://podman.io)

* Set some environment variables

        export GITLAB_USERNAME="Your GitLab username"

        # Create a personal access token on GitLab at
        # https://gitlab.com/-/profile/personal_access_tokens
        # Give the token the `api` scope.
        export GITLAB_PASSWORD="Your GitLab personal access token"

        # Fly.io requires app names to be unique across all accounts
        # worldwide. This slug will be appended to the app names created on
        # Fly.io, and to the container names when run locally.
        export SLUG="<a short, unique string, e.g. `openssl rand -hex 4`>"

        # Create an organization on Fly.io at https://fly.io/organizations
        # Use its complete name, including numerical postfix.
        export FLY_ORGANIZATION="sumario-420"

        # Create a personal access token on Fly.io at
        # https://fly.io/user/personal_access_tokens
        export FLY_ACCESS_TOKEN="fo1_c...M"

        export POSTGRES_HOSTNAME="sumario-postgres-$SLUG.flycast"
        export POSTGRES_TCP_PORT="5432"
        export POSTGRES_USERNAME="<an unique, hard to guess string, like an uuid>"
        export POSTGRES_PASSWORD="<an unique, hard to guess string, like an uuid>"

        # https://flask.palletsprojects.com/en/2.3.x/config/#SECRET_KEY
        export SECRET_KEY="<an unique, 64 character string, e.g. `openssl rand -hex 32`>"

        # Create a server on Postmark at https://account.postmarkapp.com/servers,
        # and generate a server API Token at
        # https://account.postmarkapp.com/servers/<server-id>/credentials
        # Select `sandbox` when creating the server.
        export POSTMARK_TOKEN="7...6"

        # Create a project on Sentry at https://<org-name>.sentry.io/projects,
        # and generate a Client Key and copy its DSN under "SDK Setup" at
        # https://<org-name>.sentry.io/settings/projects/<project-name>/keys
        export SENTRY_DSN="https://9...f@o...0.ingest.sentry.io/4...8"

        # Create an API key-pair on Stripe at
        # https://dashboard.stripe.com/test/apikeys Be sure to select "test mode"
        # in the Stripe dashboard. Use the Publishable and Secret keys below.
        export STRIPE_PUBKEY="pk_test_5...q"
        export STRIPE_SECRET="sk_test_5...a"

* Start the services

  In three seperate terminal windows, run:

  * `make postgres/run`
  * `make sumario/run`
  * `make traefik/run`

* Open `http://localhost:8080`
