Run these scripts to setup environment for component development. Zip is required to compress artifacts into a single file.

```bash
export COMPONENT_NAME="com.example.HelloWorld"
export COMPONENT_VERSION="1.0.0"
export RECIPE_DIR="/opt/component_development/$COMPONENT_NAME"
export ARTIFACT_DIR="/opt/component_development/$COMPONENT_NAME/artifacts"

# Deploy
gg_dep() {
  mkdir -p /tmp/artifacts/$COMPONENT_NAME/$COMPONENT_VERSION;
  cd $ARTIFACT_DIR/$COMPONENT_NAME/$COMPONENT_VERSION && zip -r /tmp/artifacts/$COMPONENT_NAME/$COMPONENT_VERSION/$COMPONENT_NAME.zip . && cd -;
  /greengrass/v2/bin/greengrass-cli --ggcRootPath /greengrass/v2 deployment create \
  --recipeDir $RECIPE_DIR --artifactDir /tmp/artifacts \
  --merge "$COMPONENT_NAME=$COMPONENT_VERSION";
}
# remove
gg_delete() {
  /greengrass/v2/bin/greengrass-cli --ggcRootPath /greengrass/v2 deployment create \
  --remove "$COMPONENT_NAME";
}
```

The to deploy a component:

```
gg_dep
```

To delete:

```bash
gg_delete
```

To delete _and_ deploy (replace testing component with same version):

```bash
gg_delete && gg_dep
```
