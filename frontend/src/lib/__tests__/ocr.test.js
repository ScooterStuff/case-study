import { extractModelNumber } from "../ocr";

describe("extractModelNumber", () => {
  test("alphanumeric Whirlpool/Maytag-style sticker text", () => {
    const ocr = `
      WHIRLPOOL
      MODEL: WDT780SAEM1
      SERIAL: F12345678
      120V 60HZ
    `;
    expect(extractModelNumber(ocr)).toBe("WDT780SAEM1");
  });

  test("long pure-numeric Kenmore model", () => {
    const ocr = "Kenmore Refrigerator\nModel  10640262010\nSerial KX12345";
    expect(extractModelNumber(ocr)).toBe("10640262010");
  });

  test("returns null when no plausible candidate is present", () => {
    expect(extractModelNumber("just some words here")).toBeNull();
    expect(extractModelNumber("")).toBeNull();
    expect(extractModelNumber(null)).toBeNull();
    expect(extractModelNumber(undefined)).toBeNull();
  });

  test("ignores stop words like MODEL/SERIAL/MFG even if length-matched", () => {
    expect(extractModelNumber("MODEL SERIAL TYPE")).toBeNull();
  });

  test("ignores 4-digit year-shaped tokens", () => {
    expect(extractModelNumber("MFG 2019")).toBeNull();
  });

  test("ignores brand names that happen to be all-letters", () => {
    expect(extractModelNumber("WHIRLPOOL KITCHENAID")).toBeNull();
  });

  test("handles non-string input safely", () => {
    expect(extractModelNumber(42)).toBeNull();
    expect(extractModelNumber({})).toBeNull();
  });

  test("strips dashes from candidate before scoring", () => {
    expect(extractModelNumber("Model: WP-W10321304")).toBe("WPW10321304");
  });

  test("picks the alphanumeric model over surrounding short numerics", () => {
    expect(extractModelNumber("60HZ 120V WDT780SAEM1 15A")).toBe("WDT780SAEM1");
  });
});
