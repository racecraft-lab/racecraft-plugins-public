module Counter {
  var count: int

  action init = count' = 0
  action Increment = all { count < 2, count' = count + 1 }
  action Hold = all { count == 2, count' = count }
  action step = any { Increment, Hold }

  val Bounded = count >= 0 and count <= 2
  temporal EventuallyFull = eventually(count == 2)
}
