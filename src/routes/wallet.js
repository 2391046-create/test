// API 엔드포인트
import { Router } from "express";
import { createWallet } from "../xrpl/wallet.js";
import { auth } from "../middleware/auth.js";
import { db } from "../db.js";

const r = Router();

// 지갑 생성
r.post("/", auth, async (req, res, next) => {
  try {
    const { currency = "XRP" } = req.body;
    const result = await createWallet(req.user.id, currency);
    res.status(201).json(result);
  } catch (e) {
    next(e);
  }
});

// 내 지갑 목록 조회
//r.get("/", auth, async (req, res, next) => {
//try {
//const { rows } = await db.query(
//`SELECT id, xrpl_address, currency, balance, updated_at
//FROM wallets WHERE user_id = $1`,
//  [req.user.id],
//);
//res.json(rows);
//} catch (e) {
//  next(e);
//}
//});

// 내 지갑 목록 조회 (테스트용 - auth 제거)
r.post("/", async (req, res, next) => {
  try {
    const { currency = "XRP" } = req.body;
    const result = await createWallet("test-user-id", currency);
    res.status(201).json(result);
  } catch (e) {
    next(e);
  }
});

export default r;
