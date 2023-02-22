import * as os from "os"

import { OPCUAServer, DataType, Variant } from "node-opcua"

function getPercentageMemoryUsed() {
  return (os.freemem() / os.totalmem()) * 100.0
}

/**
 * @param server {OPCUAServer} server
 */
function constructAddressSpace(server: OPCUAServer) {
  const addressSpace = server.engine.addressSpace
  const namespace = addressSpace!.getOwnNamespace()

  const device = namespace.addObject({
    organizedBy: addressSpace!.rootFolder.objects,
    browseName: "MyDevice"
  })

  namespace.addVariable({
    componentOf: device,
    nodeId: "s=free_memory",
    browseName: "FreeMemory",
    dataType: "Double",
    value: {
      get: () =>
        new Variant({
          dataType: DataType.Double,
          value: getPercentageMemoryUsed()
        })
    }
  })
}

;(async () => {
  try {
    const server = new OPCUAServer({
      port: 26543,
      buildInfo: {
        productName: "Sample NodeOPCUA Server for AWS IoT SiteWise"
      }
    })

    console.log("Initialising server... (please wait) ")

    await server.initialize()

    constructAddressSpace(server)

    console.log("Starting server... (please wait) ")

    await server.start()

    console.log("Server is now listening... (press CTRL+C to stop) ")

    const endpointUrl =
      server.endpoints[0].endpointDescriptions()[0].endpointUrl

    console.log(" the primary server endpoint url is ", endpointUrl)

    process.on("SIGINT", async () => {
      await server.shutdown()
      console.log("Terminated")
    })
  } catch (err) {
    console.log(err)
    process.exit(-1)
  }
})()
