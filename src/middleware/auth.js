import pkg from 'jsonwebtoken'
import 'dotenv/config'

const { verify } = pkg

export function auth(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1]
  if (!token) return res.status(401).json({ error: '인증 필요' })
  try {
    req.user = verify(token, process.env.JWT_SECRET)
    next()
  } catch {
    res.status(401).json({ error: '토큰 만료' })
  }
}
