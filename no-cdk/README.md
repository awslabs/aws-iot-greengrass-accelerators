# CDK-Less Greengrass Version 2 Accelerators

This version of the accelerators is meant to target systems with limited capabilities where is not possible to install docker locally (for custom resource deployment). For example, windows 10 gateways, where the Linux subsystem, needed to run containers, is not present, either for limitation in the hardware or because they host a custom Windows OS version where for security reasons is not possible to run linux containers.

The accelerators consist in 5 python scripts performing:
* Resource deployment/deletion for Greengrass on docker
* components deployment/deletion
* Windows native greengrass installation


## Prerequisites

- Python 3.7 or later
- Docker (any version)
- (optional) aws cli
- (windows only) Java Runtime Environment (JRE) version 8 or greater. 

## 1. Installing Greengrass on docker (Linux/MacOS)

```bash
python3 gg-docker-deploy.py <thing name>
```

The command above creates the following resources:
* an IoT "thing" called <thing name> associated to the greengrass instance
* an IoT policy to define which IoT actions are permitted to the greengrass instance
* a certificate and a private key to identify the greengrass instance
* a Role Alias for the Role that the greengrass instance can assume to access AWS services
* a thing group called <thing name>-group

All resources ids created by the script will be tracked in 'resources/manifest.json'.
The certificate and private key will be stored in 'docker/certs' together with the AmazonCA root certificate. They will be used by the Greengrass installer to enable the connection to IoT core broker.

The *gg-docker-deploy.py* will create an additional configuration file in 'docker/config/config.yaml', similar to the one below:

```
---
system:
  certificateFilePath: /tmp/certs/device.pem.crt
  privateKeyPath: /tmp/certs/private.pem.key
  rootCaPath: /tmp/certs/AmazonRootCA1.pem
  rootpath: /greengrass/v2
  thingName: <thing name>
services:
  aws.greengrass.Nucleus:
    configuration:
      mqtt:
        port: 8883
      awsRegion: us-west-2
      iotRoleAlias: <thing name>-ggRoleAliasName
      iotDataEndpoint: xxxxxxxxxxx-ats.iot.<region>.amazonaws.com
      iotCredEndpoint: xxxxxxxx.credentials.iot.<region>.amazonaws.com
    componentType: NUCLEUS
    version: 2.11.2
```

## 2. Running Greengrass in docker

Similarly to the other accelerators, the Graangrass instance can be execute with the following commands.

```bash
cd docker
docker compose up
```

## 3. Cleaning up Greengrass environment

To delete all resources create by the previous script, simply execute:

```bash
python3 gg-docker-destroy.py
```

The script relies on the content of the file 'resources/manifest.json' to remove all cloud resources created in the previous step.

## Windows native installation

Before running the windows native installation we must create a Windows user to run greengrass components:
```bash
net user /add ggc_user <some password>
```

Use Microsoft's PsExec utility https://docs.microsoft.com/en-us/sysinternals/downloads/psexec  to store the username and password for ggc_user in the Credential Manager instance for the LocalSystem account on your Windows device.

```bash
psexec -s cmd /c cmdkey /generic:ggc_user /user:ggc_user /pass:<some password>
```

For Windows systems that do not support docker linux containers, the following script takes care of running the greengrass installer, using the same configuration files created in paragraph #1 above.

```bash
python win-gg-installer.py
```

The script must be executed with Admin rights and if there is a pre-existent greengrass instance running on the same machine, it has to be stopped using:

```bash
sc stop greengrass
```

To check if the installation succeeded, please, check the status of the greengrass service:
```bash
sc query greengrass
```

# Component framework

The accelerator defines a simplified way of implementing and deployment Greengrass components:
1. The components are defined in a subfolder of ***ggComponents***. 
2. The subfolder name *is* the name of the component and **MUST** contain a "recipe.yaml" file defining the component version, behaviour, lifecycle, etc. and an "artifacts" subfolder with all executables, scripts, libraries, etc. implementing the component behaviour.

The accelerator comes with a "HelloWorld" component, writing a message on the component log, and a simulated environmental sensor, publishing a payload containing Temperature, humidity luminosity and a timestamp.

This is how the resulting directory hierarchy looks like:
```
├── ggComponents
│   ├── EnvironmentalSensor
│   │   ├── artifacts
│   │   ├── recipe.yaml
│   ├── HelloWorld
│   │   ├── artifacts
│   │   ├── recipe.yaml
```

## Component deployment

A greengrass deployment is defined by:

1. a deployment target, either a single "thing" or a "thing group"
2. a list of components 

Both information are to be defined in the file "gg-config/gg-config.yaml". The script defined in paragraph 1., takes care of defining the deployment target (either a single thing or a thing group). 
The component list must be specified manually depending as indicated below:

```yaml
---
thingArn: arn:aws:iot:<region>:<account>:thing/<thing name>
thingGroupArn: arn:aws:iot:<region>:<account>:thinggroup/<thing group name>
thingName: <thing name>
components:
- HelloWorld
- EnvironmentalSensor
```


***Although the first 3 items of the gg-config.yaml file are automatically defined by the gg-docker-deploy.py script, the deployment framework can be used also for existing greengrass groups or single instances.***

### Component deployment

Once defined the target, either a single instance or a group (if both are defined, the group takes the priority), and the list of components, the greegrass deployment can be executed by:
```bash
python3 compdeploy.py
```

### Component deletion

To cancel a deployment and all components associated to it, execute:

```bash
python3 compdestroy.py
```

