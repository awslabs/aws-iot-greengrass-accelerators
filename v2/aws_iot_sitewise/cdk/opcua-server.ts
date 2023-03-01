// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as chalk from "chalk"
import * as _ from "lodash"

import { OPCUAServer, DataType, Variant } from "node-opcua"

const browseName = "AnyCompany"
const server = new OPCUAServer({
  port: 26543,
  buildInfo: {
    productName: "Sample NodeOPCUA Server for AWS IoT SiteWise"
  }
})

function dumpObject(obj: any) {
  function w(str: string, width: number) {
    const tmp = str + "                                        "
    return tmp.substr(0, width)
  }

  return _.map(obj, function (value, key) {
    return (
      "      " +
      w(key, 30) +
      "  : " +
      (value === null ? null : value.toString())
    )
  }).join("\n")
}

console.log(chalk.yellow("  server PID          :"), process.pid)

server.start(() => {
  const endpointUrl = server.endpoints[0].endpointDescriptions()[0].endpointUrl

  console.log(
    chalk.yellow("  server on port      :"),
    server.endpoints[0].port.toString()
  )
  console.log(chalk.yellow("  endpointUrl         :"), endpointUrl)

  console.log(chalk.yellow("  serverInfo          :"))
  console.log(dumpObject(server.serverInfo))
  console.log(chalk.yellow("  buildInfo           :"))
  console.log(dumpObject(server.engine.buildInfo))

  console.log(
    chalk.yellow("\n  server now waiting for connections. CTRL+C to stop")
  )
})

server.on("post_initialize", function () {
  const addressSpace = server.engine.addressSpace
  const namespace = addressSpace!.getOwnNamespace()
  const myDevices = namespace.addFolder(addressSpace!.rootFolder.objects, {
    browseName: browseName
  })
  const variable1 = namespace.addVariable({
    organizedBy: myDevices,
    browseName: "1/Generator/FanSpeed",
    nodeId: "ns=1;s=1/Generator/FanSpeed",
    dataType: "Double",
    value: new Variant({ dataType: DataType.Double, value: 1000.0 })
  })

  setInterval(function () {
    const fluctuation = Math.random() * 100 - 50
    variable1.setValueFromSource(
      new Variant({ dataType: DataType.Double, value: 1000.0 + fluctuation })
    )
  }, 10000)

  const variable2 = namespace.addVariable({
    organizedBy: myDevices,
    browseName: "2/Generator/FanSpeed",
    nodeId: "ns=1;s=2/Generator/FanSpeed",
    dataType: "Double",
    value: new Variant({ dataType: DataType.Double, value: 1000.0 })
  })

  setInterval(function () {
    const fluctuation = Math.random() * 100 - 50
    variable2.setValueFromSource(
      new Variant({ dataType: DataType.Double, value: 1000.0 + fluctuation })
    )
  }, 10000)
})

server.on("newChannel", function (channel) {
  console.log(
    chalk.bgYellow("Client connected with address = "),
    channel.remoteAddress,
    " port = ",
    channel.remotePort
  )
})

server.on("closeChannel", function (channel) {
  console.log(
    chalk.bgCyan("Client disconnected with address = "),
    channel.remoteAddress,
    " port = ",
    channel.remotePort
  )
  if (global.gc) {
    global.gc()
  }
})

process.on("SIGINT", function () {
  console.error(chalk.red.bold(" Received server interruption from user "))
  console.error(chalk.red.bold(" shutting down ..."))
  server.shutdown(1000, function () {
    console.error(chalk.red.bold(" shutting down completed "))
    console.error(chalk.red.bold(" done "))
    console.error("")
    process.exit(-1)
  })
})
