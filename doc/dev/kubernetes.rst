Deploying to Kubernetes
========================

The provided docker file is ready to be built and deployed to Kubernetes.

At this stage, the project does not provide pre-build containers, but PR to add it to GitHub actions are welcome.

This section assumes that you built the `production` docker layer and have it in your container registry and you know how to deploy your YAML manifests to Kubernetes (e.g with FluxCD).

There are many ways to store the necessary secrets, configuration and everything in Kubernetes. This guide provides the bare minimum.

Configurations
---------------

```yaml
# Based on https://gpoddernet.readthedocs.io/en/latest/dev/configuration.html#configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: gpodder-app-config
data:
  DJANGO_CONFIGURATION: Prod
  ADMINS: 'Your Name <you@example.com>'
  ALLOWED_HOSTS: '*'
  DEFAULT_BASE_URL: 'https://gpodder.example.com'
  # GOOGLE_ANALYTICS_PROPERTY_ID
  # MAINTENANCE
  DEBUG: "true"
  DEFAULT_FROM_EMAIL: "daemon@example.com"
  SERVER_EMAIL: "daemon@example.com"
  BROKER_POOL_LIMIT: "10"
  # CACHE_BACKEND: "django.core.cache.backends.db.DatabaseCache"
  # ACCOUNT_ACTIVATION_DAYS
  PODCAST_SLUG_SUBSCRIBER_LIMIT: "1"
  MIN_SUBSCRIBERS_CATEGORY: "1"
  # INTERNAL_IPS: 
```

Secrets
--------

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gpodder
spec:
  encryptedData:
    BROKER_URL: <base64 encoded data>
    EMAIL_HOST: <base64 encoded data>
    EMAIL_HOST_PASSWORD: <base64 encoded data>
    EMAIL_HOST_USER: <base64 encoded data>
    SECRET_KEY: <base64 encoded data>
    STAFF_TOKEN: <base64 encoded data>
    SUPPORT_URL: <base64 encoded data>
    DATABASE_URL: <base64 encoded data>
    AWS_ACCESS_KEY_ID: <base64 encoded data>
    AWS_S3_ENDPOINT_URL: <base64 encoded data>
    AWS_S3_ENDPOINT_URL: <base64 encoded data>

Jobs
----

As Kubernetes Jobs are immutable. It's up to you how you re-run them on changes. This guide does not help with it. A possible approach [using FluxCD is described here](https://fluxcd.io/flux/use-cases/running-jobs/.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: collectstatics
  labels:
    app.kubernetes.io/component: collectstatics
spec:
  template:
    spec:
      serviceAccountName: gpodder
      containers:
      - name: gpodder-migrate
        image: registry.gitlab.com/nagyv/gpodder/gpodder:latest
        command: ["python",  "manage.py", "collectstatic", "--no-input"]
        envFrom: 
          - secretRef: 
              name: gpodder
          - configMapRef:
              name: gpodder-app-config
        securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
              - ALL
            privileged: false
            readOnlyRootFilesystem: true
      restartPolicy: Never
```

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: gpodder-migrate
  labels:
    app.kubernetes.io/component: db-migrate
spec:
  # ttlSecondsAfterFinished does not work well with GitOps as the Job is deleted
  # ttlSecondsAfterFinished: 200
  template:
    metadata:
      labels:
        app.kubernetes.io/component: db-migrate
    spec:
      serviceAccountName: gpodder
      containers:
      - name: gpodder-migrate
        image: registry.gitlab.com/nagyv/gpodder/gpodder:latest
        command: ["python",  "manage.py", "migrate"]
        envFrom: 
          - secretRef: 
              name: gpodder
          - configMapRef:
              name: gpodder-app-config
        securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
              - ALL
            privileged: false
            readOnlyRootFilesystem: true
      restartPolicy: Never
```

Deployment
-----------

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gpodder
  labels:
    app.kubernetes.io/component: webapp
spec:
  selector:
    matchLabels:
      app.kubernetes.io/component: webapp
  template:
    metadata:
      labels:
        app.kubernetes.io/component: webapp
    spec:
      serviceAccountName: gpodder
      containers:
      - name: gpodder
        image: registry.example.com/gpodder/gpodder:latest
        imagePullPolicy: Always
        resources: {}
          # limits:
          #   memory: "128Mi"
          #   cpu: "500m"
        # livenessProbe:
        #   httpGet:
        #     path: /ht/
        #     port: 8000
        #     httpHeaders:
        #       - name: Host
        #         value: gpodder.nagyv.com
        #   initialDelaySeconds: 15
        #   periodSeconds: 10
        #   successThreshold: 1
        #   failureThreshold: 2
        #   timeoutSeconds: 3
        readinessProbe:
          httpGet:
            path: /ht/
            port: 8000
            httpHeaders:
              - name: Host
                value: gpodder.nagyv.com
          initialDelaySeconds: 10
          timeoutSeconds: 3
        ports:
        - containerPort: 8000
        envFrom: 
          - secretRef: 
              name: gpodder
          - configMapRef:
              name: gpodder-app-config
        securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
              - ALL
            privileged: false
            readOnlyRootFilesystem: true
      securityContext:
        {}
```

Service
-------

```yaml
apiVersion: v1
kind: Service
metadata:
  name: gpodder
spec:
  selector: {}
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
```
