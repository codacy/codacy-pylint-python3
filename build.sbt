lazy val `doc-generator` = project
  .settings(
    libraryDependencies ++= Seq(
      "net.ruippeixotog" %% "scala-scraper" % "3.0.0",
      "com.github.pathikrit" %% "better-files" % "3.8.0",
      "com.lihaoyi" %% "ujson" % "0.8.0"
    ),
    scalaVersion := "2.13.2",
    Compile / fork := true
  )
