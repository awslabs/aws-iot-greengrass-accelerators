import { expect as expectCDK, matchTemplate, MatchStyle, SynthUtils } from "@aws-cdk/assert"
import * as cdk from "aws-cdk-lib"
import { SiteWiseStack } from "../lib/SiteWiseStack"

const scope = new cdk.Stack()
const _stack = new SiteWiseStack(scope, "mystack", {})
const stack = SynthUtils.toCloudFormation(scope)

test("create the stack", () => {
  expect(_stack).not.toBeNull()
  expect(stack).not.toBeNull()
})
