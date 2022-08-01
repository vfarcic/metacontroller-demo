from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from re import L

class Controller(BaseHTTPRequestHandler):
  def sync(self, parent, children):
    # Compute status based on observed state.
    desired_status = {
      "deployments": len(children["Deployment.apps/v1"]),
      "services": len(children["Service.v1"]),
      "ingresses": len(children["Ingress.networking.k8s.io/v1"])
    }

    image = parent.get("spec", {}).get("image")
    port = parent.get("spec", {}).get("port", "80")
    cpu_limit = parent.get("spec", {}).get("cpuLimit", "500m")
    mem_limit = parent.get("spec", {}).get("memLimit", "512Mi")
    cpu_req = parent.get("spec", {}).get("cpuReq", "250m")
    mem_req = parent.get("spec", {}).get("memReq", "256Mi")
    host = parent.get("spec", {}).get("host")
    replicas = parent.get("spec", {}).get("replicas")
    desired_resources = [
      {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
          "name": parent["metadata"]["name"],
          "labels": {
            "app.kubernetes.io/name": parent["metadata"]["name"]
          }
        },
        "spec": {
          "replicas": replicas,
          "selector": {
            "matchLabels": {
              "app.kubernetes.io/name": parent["metadata"]["name"]
            }
          },
          "template": {
            "metadata": {
              "labels": {
                "app.kubernetes.io/name": parent["metadata"]["name"]
              }
            },
            "spec": {
              "containers": [
                {
                  "name": "main",
                  "image": image,
                  "ports": [
                    {
                      "containerPort": port
                    }
                  ],
                  "resources": {
                    "limits": {
                      "cpu": cpu_limit,
                      "memory": mem_limit
                    },
                    "requests": {
                      "cpu": cpu_req,
                      "memory": mem_req
                    }
                  }
                }
              ]
            }
          }
        }
      },
      {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
          "name": parent["metadata"]["name"],
          "labels": {
            "app.kubernetes.io/name": parent["metadata"]["name"]
          }
        },
        "spec": {
          "type": "ClusterIP",
          "ports": [
            {
              "port": port,
              "targetPort": port,
              "protocol": "TCP",
              "name": "http"
            }
          ],
          "selector": {
            "app.kubernetes.io/name": parent["metadata"]["name"]
          }
        }
      },
      {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
          "name": parent["metadata"]["name"],
          "labels": {
            "app.kubernetes.io/name": parent["metadata"]["name"]
          },
          "annotations": {
            "ingress.kubernetes.io/ssl-redirect": "false"
          }
        },
        "spec": {
          "rules": [
            {
              "http": {
                "paths": [
                  {
                    "path": "/",
                    "pathType": "ImplementationSpecific",
                    "backend": {
                      "service": {
                        "name": parent["metadata"]["name"],
                        "port": {
                          "number": port
                        }
                      }
                    }
                  }
                ]
              },
              "host": host
            }
          ]
        }
      }
    ]

    return {"status": desired_status, "children": desired_resources}

  def do_POST(self):
    observed = json.loads(self.rfile.read(int(self.headers.get("content-length"))))
    print("xxx")
    # print(observed["children"])
    print("yyy")
    desired = self.sync(observed["parent"], observed["children"])

    self.send_response(200)
    self.send_header("Content-type", "application/json")
    self.end_headers()
    self.wfile.write(json.dumps(desired).encode())

HTTPServer(("", 80), Controller).serve_forever()
