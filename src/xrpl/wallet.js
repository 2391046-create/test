// 지갑 생성 로직
import pkg from "xrpl";
import crypto from "crypto";
import "dotenv/config";
import { getClient } from "./client.js";
import { db } from "../db.js";

const { Wallet } = pkg;

export async function createWallet(userId, currency = "XRP") {
  // 1) XRPL Testnet에서 키페어 생성 + Faucet 1000 XRP 자동 지급
  const client = await getClient();
  const { wallet, balance } = await client.fundWallet();

  // 2) seed 암호화 (절대 평문 저장 금지)
  const encrypted = encryptSeed(wallet.seed);

  // 3) DB 저장
  const { rows } = await db.query(
    `INSERT INTO wallets (user_id, xrpl_address, xrpl_secret_enc, currency, balance)
     VALUES ($1, $2, $3, $4, $5)
     RETURNING id`,
    [userId, wallet.address, encrypted, currency, balance],
  );

  return {
    walletId: rows[0].id,
    address: wallet.address,
    balance,
    currency,
  };
}

function encryptSeed(seed) {
  const key = Buffer.from(process.env.ENCRYPTION_KEY, "hex"); // 32바이트
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
  const enc = Buffer.concat([cipher.update(seed, "utf8"), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([iv, tag, enc]).toString("base64");
}
