pipeline {
  agent { label 'linux' }
  options { timestamps(); disableConcurrentBuilds() }
  triggers { pollSCM('H/2 * * * *') }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Test') { steps { sh 'mvn -B clean test' } }
    stage('Package') { steps { sh 'mvn -B -DskipTests package' } }
  }
  post {
    always { junit allowEmptyResults: true, testResults: 'target/surefire-reports/TEST-*.xml' }
    success { archiveArtifacts artifacts: 'target/convertflow.jar', fingerprint: true }
  }
}
