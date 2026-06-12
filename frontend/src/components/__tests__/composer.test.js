import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatWindow from "../ChatWindow";

jest.mock("../../lib/api", () => ({
  streamChat: jest.fn().mockResolvedValue(undefined),
  getSessionId: () => "test-session",
  newSession: () => "test-session-2",
}));
const { streamChat } = require("../../lib/api");

const setup = () => render(<ChatWindow />);

beforeEach(() => streamChat.mockClear());

test("Enter sends the message", async () => {
  setup();
  const box = screen.getByLabelText("Message");
  await userEvent.type(box, "my dishwasher is leaking{Enter}");
  expect(streamChat).toHaveBeenCalledTimes(1);
  expect(streamChat.mock.calls[0][1]).toBe("my dishwasher is leaking");
});

test("Shift+Enter inserts a newline instead of sending", async () => {
  setup();
  const box = screen.getByLabelText("Message");
  await userEvent.type(box, "line one{Shift>}{Enter}{/Shift}line two");
  expect(streamChat).not.toHaveBeenCalled();
  expect(box.value).toContain("\n");
});

test("suggested spec-query chips send on click", async () => {
  setup();
  await userEvent.click(screen.getByText("How can I install part number PS11752778?"));
  expect(streamChat).toHaveBeenCalledTimes(1);
  expect(streamChat.mock.calls[0][1]).toMatch(/PS11752778/);
});

test("photo upload button is rendered in the composer", () => {
  setup();
  expect(screen.getByLabelText(/Upload a photo/i)).toBeInTheDocument();
});
