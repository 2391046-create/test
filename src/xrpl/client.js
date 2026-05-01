// XRPL 연결
import pkg from "xrpl";
import "dotenv/config";

const { Client } = pkg;
let client = null;

export async function getClient() {
  if (client?.isConnected()) return client;
  client = new Client(process.env.XRPL_TESTNET_URL);
  await client.connect();
  return client;
}
