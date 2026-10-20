# Only the reviewed website and runtime files enter the deployment image.
# No project history, local virtualenv, Git metadata, or credentials are copied.
FROM node:24.19.0-bookworm-slim AS frontend
WORKDIR /build
RUN npm install --global pnpm@11.19.0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY tsconfig.json vite.config.ts index.html explore.html builder.html reaction-lab.html calculators.html ./
COPY src ./src
COPY public ./public
COPY scripts/compress-dist.mjs ./scripts/compress-dist.mjs
RUN pnpm build && node scripts/compress-dist.mjs

FROM python:3.12-slim-bookworm AS trial
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=10000 \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
WORKDIR /app
# RDKit's 2D drawing extension also links against the system Expat runtime.
RUN apt-get update && apt-get install -y --no-install-recommends libxrender1 libxext6 libgomp1 libexpat1 \
    && rm -rf /var/lib/apt/lists/*
COPY server/requirements.txt server/requirements-production.txt ./server/
RUN pip install --no-cache-dir --only-binary=:all: -r server/requirements-production.txt
# All existing rules, confidence assessors and mapping modules are required.
# Copy only Python runtime files, never the whole checkout or server secrets.
COPY server/*.py ./server/
# RDKit's reaction catalog imports this exact shared data at startup.
COPY src/shared-molecules.json ./src/shared-molecules.json
COPY --from=frontend /build/dist ./dist
RUN python -c "from server import chemistry_server as c; from server.reaction_information import DEFINITIONS; assert len(DEFINITIONS) == 24; assert c.reaction_catalog()['reactants']"
RUN useradd --create-home --uid 10001 capstone
USER capstone
EXPOSE 10000
CMD ["gunicorn", "--config", "server/gunicorn.conf.py", "server.production_app:create_app()"]
