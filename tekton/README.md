# Tekton

```bash
tkn -n analytics-for-spotify pipeline start analytics-for-spotify \
    --workspace=name=data,volumeClaimTemplateFile=tekton/base/pvc.yaml \
    --param="IMAGE=registry.arthurvardevanyan.com/apps/analytics-for-spotify:production" \
    --param="url=https://github.com/ArthurVardevanyan/Analytics-for-Spotify.git" \
    --showlog
```
