# CDK-Less AWS IoT Greengrass Version 2 Accelerators

This version of the accelerators aims at:
 - deploying all cloud resources needed by AWS IoT Greengrass without making use of CDK;
 - execute AWS IoT Greengrass inside a docker container, similarly to the solution contained in [v2](v2/base/docker/), if the hosting platform supports Linux containers;  
 - install and execute AWS IoT Greengrass on Windows systems that do not support Linux containers and cannot use the solution in [v2](v2/base/docker/). On such systems the use of CDK based accelerators is not possible because the accelerators use CDK custom resources that requires docker on the host platform;
 - define a simplified AWS IoT Greengrass component development framework for both docker and Windows setup;
 
The accelerators consist in 5 python scripts performing:
* Resource deployment/deletion for Greengrass on docker
* components deployment/deletion
* Windows native greengrass installation
a graphic view of accelerators can be found in [architecture](./arch.drawio.png)

## Prerequisites

- Python 3.7 or later
- Docker (any version)
- (optional) aws cli
- (Windows only) Java Runtime Environment (JRE) version 8 or greater. 

## 1. Installing AWS IoT Greengrass core resources (Linux/MacOS/Windows)

```bash
pip install -r requirements.txt
python3 gg-core-deploy.py <thing name>
```

The command above creates the following resources:
* an IoT "thing" called <thing name>-policy associated to the greengrass instance
* an IoT policy to define which IoT actions are permitted to the greengrass instance
* a certificate and a private key to identify the greengrass instance
* a Role Alias for the Role that the greengrass instance can assume to access AWS services
* a thing group called <thing name>-group

All resources ids created by the script will be tracked in 'resources/manifest.json'.
The certificate and private key will be stored in 'docker/certs' together with the AmazonCA root certificate. They will be used by the Greengrass installer to enable the connection to IoT core broker.

The *gg-core-deploy.py* will create an additional configuration file in 'docker/config/config.yaml', similar to the one below:

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

## 2. Running AWS IoT Greengrass in docker container (Mac/Linux/Windows with Linux container support)

Similarly to the other accelerators, the Greengrass instance can be executed inside a docker container with the following commands.

```bash
cd docker
docker compose up
```

## 3. Cleaning up AWS IoT Greengrass core resources

To delete all resources create by the gg-core-deploy.py script, simply execute:

```bash
python3 gg-core-destroy.py
```

The script relies on the content of the file 'resources/manifest.json' to remove all cloud resources created in the previous step.

## Running AWS IoT Greengrass on Windows native (without Linux container support)

Before running the Windows native installation script we must create a Windows user that will be assumed by AWS IoT Grengrass Nucleus to execute greengrass components:
```bash
net user /add ggc_user <some password>
```

Use Microsoft's PsExec utility https://docs.microsoft.com/en-us/sysinternals/downloads/psexec  to store the username and password for ggc_user in the Credential Manager instance for the LocalSystem account on your Windows device.

```bash
psexec -s cmd /c cmdkey /generic:ggc_user /user:ggc_user /pass:<some password>
```

For Windows systems that do not support docker Linux containers, the following script takes care of running the AWS IoT Greengrass installer, using the same configuration files created in paragraph #1 above.

```bash
pip install -r win-requirements.txt
python win-gg-installer.py
```

The script must be executed with Admin rights and if there is a pre-existent AWS IoT Greengrass instance running on the same machine, it has to be stopped using:

```bash
sc stop greengrass
```

To check if the installation succeeded, please, check the status of the AWS IoT Greengrass service:
```bash
sc query greengrass
```

# Component framework

The accelerator defines a simplified framwork of developing AWS IoT Greengrass components:
1. The components are defined in a subfolder of ***ggComponents***. 
2. The subfolder name *is* the name of the component and **MUST** contain a "recipe.yaml" file defining the component version, behaviour, lifecycle, etc. and an "artifacts" subfolder with all executables, scripts, libraries, etc. implementing the component behaviour.

The accelerator comes with a "HelloWorld" component, writing a message on the component log, and an "EnvironmentaSensor" component, publishing a payload containing Temperature, humidity luminosity and a timestamp, simulating a typical environmental sensor.

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

A AWS IoT Greengrass deployment is defined by:

1. a deployment target, either a single "thing" or a "thing group"
2. a list of components 

Both information are to be defined in the file "gg-config/gg-config.yaml". The script defined in paragraph 1., takes care of defining the deployment target (either a single thing or a thing group). 
The component list must be specified manually in the "component" section of the yaml file as indicated below:

```yaml
---
thingArn: arn:aws:iot:<region>:<account>:thing/<thing name>
thingGroupArn: arn:aws:iot:<region>:<account>:thinggroup/<thing group name>
thingName: <thing name>
components:
- HelloWorld
- EnvironmentalSensor
```


***Although the first 3 items of the gg-config.yaml file are automatically defined by the gg-docker-deploy.py script, the deployment framework can be used also by entering, the group name or the instance name, manually***

### Component deployment

Once defined the target, either a single instance or a group (if both are defined, the group takes the priority), and the list of components, the AWS IoT Greegrass deployment can be executed by:
```bash
python3 gg-comp-deploy.py
```

### Component deletion

To cancel a deployment and all components associated to it, execute:

```bash
python3 gg-comp-destroy.py
```

