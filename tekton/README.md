# Tekton

```bash
tkn -n analytics-for-spotify pipeline start analytics-for-spotify \
    --workspace=name=data,volumeClaimTemplateFile=tekton/base/pvc.yaml \
    --param="IMAGE=registry.arthurvardevanyan.com/apps/analytics-for-spotify:production" \
    --param="git-url=https://github.com/ArthurVardevanyan/Analytics-for-Spotify.git" \
    --param="git-name=ArthurVardevanyan/Analytics-for-Spotify" \
    --param="git-commit=$(git log --format=oneline | cut -d ' ' -f 1 | head -n 1)"
    --showlog
```
