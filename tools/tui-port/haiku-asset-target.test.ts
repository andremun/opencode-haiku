import { expect, test } from "bun:test"
import { getNativeAssetDescriptor } from "../../source/opentui-6f0efd3330978d696b42db3d7d95d2042008312b/packages/core/src/node-asset-target"

test("Haiku resolves its own native renderer without selecting a Linux artifact", () => {
  expect(getNativeAssetDescriptor({ platform: "haiku" as never, arch: "x64" })).toEqual({
    key: "@opentui/core-haiku-x64/libopentui.so",
    packageName: "@opentui/core-haiku-x64",
    fileName: "libopentui.so",
  })
  expect(() => getNativeAssetDescriptor({ platform: "haiku" as never, arch: "x64", libc: "musl" })).toThrow()
})
