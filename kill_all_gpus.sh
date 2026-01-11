nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits | awk 'NF' | sort -u | xargs -r kill -9
