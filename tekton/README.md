# Tekton

```bash
tkn -n analytics-for-spotify pipeline start image-build -s pipeline \
  --param="IMAGE=registry.arthurvardevanyan.com/apps/analytics-for-spotify:base" \
  --param="git-url=https://git.arthurvardevanyan.com/ArthurVardevanyan/Analytics-for-Spotify" \
  --param="git-commit=$(git log --format=oneline | cut -d ' ' -f 1 | head -n 1)" \
  --param="DOCKERFILE=./container/containerfile" \
  --workspace=name=data,volumeClaimTemplateFile=tekton/base/pvc.yaml \
  --showlog

tkn -n analytics-for-spotify pipeline start analytics-for-spotify -s pipeline \
    --workspace=name=data,volumeClaimTemplateFile=tekton/base/pvc.yaml \
    --param="IMAGE=registry.arthurvardevanyan.com/apps/analytics-for-spotify:develop" \
    --param="git-url=https://git.arthurvardevanyan.com/ArthurVardevanyan/Analytics-for-Spotify" \
    --param="git-name=ArthurVardevanyan/Analytics-for-Spotify" \
    --param="git-ref=refs/heads/develop"\
    --param="git-commit=$(git log --format=oneline | cut -d ' ' -f 1 | head -n 1)" \
    --showlog
```
