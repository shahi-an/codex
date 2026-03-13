pipeline {

 agent any

 environment {
  REGISTRY = "34.30.178.105:8082"
  IMAGE = "maid-app"
 }

 stages {

  stage('Build Docker Image') {
   steps {
    sh 'docker build -t $IMAGE .'
   }
  }

  stage('Tag Image') {
   steps {
    sh 'docker tag $IMAGE $REGISTRY/$IMAGE:${BUILD_NUMBER}'
   }
  }

  stage('Docker Login') {
   steps {
    withCredentials([usernamePassword(
        credentialsId: 'Nexus-docker',
        usernameVariable: 'USER',
        passwordVariable: 'PASS'
    )]) {

      sh 'echo $PASS | docker login $REGISTRY -u $USER --password-stdin'
    }
   }
  }

  stage('Push Image') {
   steps {
    sh 'docker push $REGISTRY/$IMAGE:${BUILD_NUMBER}'
   }
  }

 }

}

