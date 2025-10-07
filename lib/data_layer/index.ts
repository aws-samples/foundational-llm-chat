import { Construct } from "constructs";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as s3 from "aws-cdk-lib/aws-s3";
import { RemovalPolicy } from "aws-cdk-lib";

export interface DataLayerProps {
  readonly prefix: string; // Prefix from the configuration
}

export class DataLayer extends Construct {
  public readonly table: dynamodb.Table;
  public readonly bucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: DataLayerProps) {
    super(scope, id);

    this.table = new dynamodb.Table(this, "DynamoDBTableDataLayer", {
      tableName: `${props.prefix.toLowerCase()}-ffchat-table`,
      partitionKey: {
        name: "PK",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "SK",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: RemovalPolicy.DESTROY,
    });

    this.table.addGlobalSecondaryIndex({
      indexName: "UserThread",
      partitionKey: {
        name: "UserThreadPK",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "UserThreadSK",
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.INCLUDE,
      nonKeyAttributes: ["id", "name"],
    });

    this.bucket = new s3.Bucket(this, "BucketS3DataLayer", {
      bucketName: `${props.prefix.toLowerCase()}-ffchat-bucket-${Math.floor(Math.random() * (10000 - 100) + 100)}`,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      enforceSSL: true, // Enforce SSL/TLS for all requests
      encryption: s3.BucketEncryption.S3_MANAGED, // Enable server-side encryption
    });
  }
}
