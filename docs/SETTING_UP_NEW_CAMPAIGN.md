1. If you need a new URL add a new `CNAME` record in greengeeks that points to `dpnk.dopracenakole.cz`. Only urls in the form of `<slug>.dopracenakole.cz` are supported.
2. Add a new campaign in the admin and set the slug to the subdomain you just configured.
3. Add new host into DO k8 ingress NGNIX [config file](https://github.com/auto-mat/k8s/blob/master/manifests/ingress/ngnix.yaml).
