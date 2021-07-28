import { expect as expectCDK, matchTemplate, MatchStyle, SynthUtils } from "@aws-cdk/assert"
import * as cdk from "@aws-cdk/core"
import { SsmComponentStack } from "../lib/SsmComponentStack"

const scope = new cdk.Stack()
const _stack = new SsmComponentStack(scope, "mystack", {})
const stack = SynthUtils.toCloudFormation(scope)

test("create the stack", () => {
  expect(_stack).not.toBeNull()
  expect(stack).not.toBeNull()
})
